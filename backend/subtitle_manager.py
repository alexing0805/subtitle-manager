import os
import asyncio
import json
import hashlib
import random
import re
import shutil
import time
from html import unescape
from datetime import datetime
from typing import List, Optional, Set, Dict, Any
from pathlib import Path
from urllib.parse import quote, urljoin
import xml.etree.ElementTree as ET
from loguru import logger
import aiohttp
import chardet

from backend.config import settings, Config, reload_settings
import backend.tmdb_api as tmdb_module

# 创建全局配置实例
config = Config()

# 初始化 TMDB API - 使用重新加载后的配置
fresh_settings = reload_settings()
tmdb_module.init_tmdb_api(fresh_settings.TMDB_API_KEY)

from backend.utils import (
    get_video_files, has_chinese_subtitle, extract_video_info,
    get_subtitle_save_path, is_movie_file, is_tv_episode,
    format_title_for_search, get_plex_subtitle_filename
)
from backend.subtitle_sources import get_source, SubtitleResult, normalize_release_text, score_release_title
from backend.nfo_parser import NFOParser


class SubtitleManager:
    """字幕管理器"""

    # 任务队列持久化文件
    TASK_QUEUE_FILE = "/app/data/task_queue.json"

    def __init__(self):
        self.processed_files: Set[str] = set()
        self.failed_files: dict = {}  # 记录失败次数
        self.history_file = "/app/data/history.json"
        self._auto_request_lock = asyncio.Lock()
        self._next_auto_request_at = 0.0
        # 从配置加载库缓存 TTL（默认 10 分钟）
        self._library_cache_ttl: float = float(getattr(settings, 'LIBRARY_CACHE_TTL', 600))
        self._library_cache: Dict[str, Dict[str, Any]] = {
            "movies": {"expires_at": 0.0, "data": None},
            "tvshows": {"expires_at": 0.0, "data": None},
            "anime": {"expires_at": 0.0, "data": None},
        }
        # 任务队列状态
        self._task_queue: List[Dict[str, Any]] = []
        self._current_scan_task: Optional[asyncio.Task] = None
        self._scan_progress: Dict[str, Any] = {
            "isScanning": False,
            "progress": 0,
            "currentFile": "",
            "totalFiles": 0,
            "processedFiles": 0,
        }
        # 字幕格式加分配置
        self._subtitle_format_bonus_config: Dict[str, float] = self._parse_subtitle_format_bonus()
        self.load_history()
        self._load_task_queue()

    def _parse_subtitle_format_bonus(self) -> Dict[str, float]:
        """
        解析字幕格式加分配置
        配置格式: "srt=0.08,ass=0.06,vtt=0.03,sup=-0.16"
        """
        config_str = getattr(settings, 'SUBTITLE_FORMAT_BONUS', 'srt=0.08,ass=0.06,ssa=0.06,vtt=0.03,smi=0.03,sami=0.03,sup=-0.16,idx=-0.16,sub=-0.16')
        result = {}
        try:
            for item in config_str.split(','):
                item = item.strip()
                if '=' in item:
                    fmt, bonus = item.split('=', 1)
                    result[fmt.strip().lower()] = float(bonus.strip())
        except Exception as e:
            logger.warning(f"解析字幕格式加分配置失败，使用默认值: {e}")
            result = {"srt": 0.08, "ass": 0.06, "ssa": 0.06, "vtt": 0.03, "smi": 0.03, "sami": 0.03, "sup": -0.16, "idx": -0.16, "sub": -0.16}
        return result

    def _generate_task_id(self) -> str:
        """生成唯一任务 ID"""
        return hashlib.md5(f"{time.time()}-{random.random()}".encode()).hexdigest()[:12]

    def _load_task_queue(self):
        """从文件加载任务队列"""
        try:
            if os.path.exists(self.TASK_QUEUE_FILE):
                with open(self.TASK_QUEUE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._task_queue = data.get('tasks', [])
                    logger.info(f"已加载任务队列: {len(self._task_queue)} 个待处理任务")
        except Exception as e:
            logger.error(f"加载任务队列失败: {e}")
            self._task_queue = []

    def _save_task_queue(self):
        """保存任务队列到文件"""
        try:
            os.makedirs(os.path.dirname(self.TASK_QUEUE_FILE), exist_ok=True)
            with open(self.TASK_QUEUE_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'tasks': self._task_queue,
                    'last_update': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务队列失败: {e}")

    def load_history(self):
        """加载处理历史"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get('processed', []))
                    self.failed_files = data.get('failed', {})
                    logger.info(f"已加载历史记录: {len(self.processed_files)} 个文件已处理")
        except Exception as e:
            logger.error(f"加载历史记录失败: {e}")
    
    def save_history(self):
        """保存处理历史"""
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed': list(self.processed_files),
                    'failed': self.failed_files,
                    'last_update': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")

    async def _throttle_auto_requests(self, phase: str, video_label: str):
        """Spread automatic subtitle requests to avoid source-side rate limits."""
        min_delay = max(0, int(settings.AUTO_DOWNLOAD_DELAY_MIN_SECONDS))
        max_delay = max(min_delay, int(settings.AUTO_DOWNLOAD_DELAY_MAX_SECONDS))
        if max_delay <= 0:
            return

        loop = asyncio.get_running_loop()
        async with self._auto_request_lock:
            now = loop.time()
            scheduled_at = self._next_auto_request_at or now
            jitter = random.uniform(min_delay, max_delay)
            wait_time = max(0.0, scheduled_at - now) + jitter
            self._next_auto_request_at = now + wait_time

        logger.info(
            f"自动下载节流: {phase}, 媒体={video_label}, 延迟 {wait_time:.1f}s 以避免字幕源限流"
        )
        await asyncio.sleep(wait_time)
    
    async def scan_and_process(self):
        """扫描并处理所有监控目录"""
        logger.info("开始扫描监控目录...")
        
        all_video_files = []
        watch_dirs = settings.get_watch_dirs()
        logger.info(f"监控目录: {watch_dirs}")
        for watch_dir in watch_dirs:
            if os.path.exists(watch_dir):
                video_files = get_video_files(watch_dir)
                all_video_files.extend(video_files)
                logger.info(f"目录 {watch_dir} 找到 {len(video_files)} 个视频文件")
            else:
                logger.warning(f"监控目录不存在: {watch_dir}")
        
        # 过滤已处理的文件
        new_files = []
        for video_path in all_video_files:
            file_hash = self._get_file_hash(video_path)
            if file_hash not in self.processed_files:
                # 检查失败次数
                fail_count = self.failed_files.get(file_hash, 0)
                if fail_count < 3:  # 最多重试3次
                    new_files.append(video_path)
                else:
                    logger.debug(f"跳过失败次数过多的文件: {video_path}")
        
        logger.info(f"发现 {len(new_files)} 个新文件需要处理")
        
        # 并发处理
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_DOWNLOADS)
        tasks = []
        for video_path in new_files:
            task = self._process_video_with_semaphore(semaphore, video_path)
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            fail_count = sum(1 for r in results if r is False or isinstance(r, Exception))
            logger.info(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
        
        self.save_history()
    
    def _get_file_hash(self, video_path: str) -> str:
        """获取文件标识（路径+大小+修改时间）"""
        try:
            stat = os.stat(video_path)
            return f"{video_path}:{stat.st_size}:{stat.st_mtime}"
        except:
            return video_path
    
    async def _process_video_with_semaphore(self, semaphore: asyncio.Semaphore, video_path: str):
        """使用信号量限制并发处理视频"""
        async with semaphore:
            return await self._process_video(video_path)
    
    async def _process_video(self, video_path: str) -> bool:
        """处理单个视频文件"""
        file_hash = self._get_file_hash(video_path)
        
        try:
            logger.info(f"处理文件: {video_path}")
            
            # 检查是否已有中文字幕
            if has_chinese_subtitle(video_path):
                logger.info(f"已有中文字幕，跳过: {video_path}")
                self.processed_files.add(file_hash)
                return True
            
            # 提取视频信息
            video_info = extract_video_info(video_path)
            logger.info(f"视频信息: {video_info['name']}, 年份: {video_info.get('year')}, "
                       f"分辨率: {video_info.get('resolution')}, 来源: {video_info.get('source')}")
            
            # 搜索字幕
            await self._throttle_auto_requests("搜索字幕", video_info['name'])
            subtitles = await self._search_subtitles(video_info)
            
            if not subtitles:
                logger.warning(f"未找到匹配的字幕: {video_info['name']}")
                self._record_failure(file_hash)
                return False
            
            # 按评分排序
            subtitles.sort(key=lambda x: x.score, reverse=True)
            
            # 尝试下载最佳匹配的字幕
            for subtitle in subtitles[:3]:  # 尝试前3个
                logger.info(f"尝试下载字幕: {subtitle.title} (来源: {subtitle.source}, 匹配度: {subtitle.score:.2f})")
                
                save_path = get_subtitle_save_path(video_path, subtitle.language)
                
                source = get_source(subtitle.source.lower())
                if source:
                    before_paths = set(self._get_subtitle_candidates(video_path))
                    await self._throttle_auto_requests("下载字幕", video_info['name'])
                    download_state = await source.download(subtitle, save_path)
                    if download_state:
                        actual_path = self._resolve_downloaded_subtitle_path(
                            download_result=download_state,
                            video_path=video_path,
                            requested_path=save_path,
                            before_paths=before_paths,
                        )
                        if not actual_path:
                            logger.warning("字幕下载成功但未找到保存文件，尝试下一个结果")
                            continue
                        normalized = self._normalize_downloaded_subtitle(video_path, actual_path)
                        plex_refresh = await self._refresh_plex_media(video_path)
                        # 验证下载的字幕
                        if has_chinese_subtitle(video_path):
                            self._mark_cached_video_has_subtitle(video_path, True)
                            logger.info(f"字幕下载并验证成功: {normalized['path']} (plex={plex_refresh})")
                            self.processed_files.add(file_hash)
                            # 清除失败记录
                            if file_hash in self.failed_files:
                                del self.failed_files[file_hash]
                            return True
                        else:
                            logger.warning(f"下载的字幕验证失败，尝试下一个")
                            # 删除无效字幕文件
                            try:
                                if os.path.exists(actual_path):
                                    os.remove(actual_path)
                            except:
                                pass
            
            logger.error(f"所有字幕源均下载失败: {video_info['name']}")
            self._record_failure(file_hash)
            return False
            
        except Exception as e:
            logger.error(f"处理视频异常: {video_path}, 错误: {e}")
            self._record_failure(file_hash)
            return False
    
    async def _search_subtitles(self, video_info: dict) -> List[SubtitleResult]:
        """从多个源搜索字幕，使用 NFO 和 TMDB 信息增强搜索结果"""
        all_results = []

        subtitle_sources = settings.get_subtitle_sources()
        logger.info(f"开始搜索字幕，视频: {video_info.get('name')}, 可用字幕源: {subtitle_sources}")

        # 检查是否有 NFO 信息
        nfo_info = video_info.get('nfo')
        if nfo_info:
            logger.info(f"使用 NFO 文件信息: TMDB ID={nfo_info.get('tmdbid')}, IMDB ID={nfo_info.get('imdbid')}")

        # 如果有 NFO 中的 TMDB ID（对于 TV 剧集使用 series-level TMDB ID），直接使用
        # 注意：video_info['series_tmdb_id'] 是从 series-level NFO 获取的正确 TMDB ID
        # 如果存在，优先使用它来查询 TMDB（因为 episode-level NFO 的 ID 可能是错误的）
        query_tmdb_id = video_info.get('series_tmdb_id') or video_info.get('tmdb_id')
        logger.info(f"[DEBUG] query_tmdb_id={query_tmdb_id}, series_tmdb_id={video_info.get('series_tmdb_id')}, tmdb_id={video_info.get('tmdb_id')}, TMDB_API_KEY configured={bool(settings.TMDB_API_KEY and tmdb_module.tmdb_api.api_key)}")
        if query_tmdb_id and settings.TMDB_API_KEY and tmdb_module.tmdb_api.api_key:
            try:
                tmdb_info = await (
                    tmdb_module.tmdb_api.get_movie_details(query_tmdb_id)
                    if video_info.get('is_movie')
                    else tmdb_module.tmdb_api.get_tv_details(query_tmdb_id)
                )
                if tmdb_info:
                    logger.info(f"通过 TMDB ID {query_tmdb_id} 获取信息成功: {tmdb_info.get('title')}")
                    video_info['tmdb_title'] = tmdb_info.get('title')
                    video_info['imdb_id'] = tmdb_info.get('imdb_id')
                    # 用 TMDB 的标题覆盖 search_names，避免 episode-level NFO 的错误标题干扰
                    if video_info.get('nfo') and tmdb_info.get('title'):
                        video_info['nfo']['search_names'] = [
                            tmdb_info['title'],
                            tmdb_info.get('original_title', tmdb_info['title']),
                        ]
                        logger.info(f"使用 TMDB 标题更新 search_names: {video_info['nfo']['search_names']}")
            except Exception as e:
                logger.warning(f"通过 TMDB ID 获取信息失败: {e}")

        # 如果没有 NFO 信息，尝试使用 TMDB API 搜索
        elif settings.TMDB_API_KEY and tmdb_module.tmdb_api.api_key:
            try:
                if video_info.get('is_movie'):
                    tmdb_info = await tmdb_module.tmdb_api.search_movie(
                        video_info.get('title', ''),
                        video_info.get('year')
                    )
                else:
                    tmdb_info = await tmdb_module.tmdb_api.search_tv(
                        video_info.get('title', ''),
                        video_info.get('year')
                    )

                if tmdb_info:
                    logger.info(f"TMDB 匹配成功: {tmdb_info.get('title')} ({tmdb_info.get('year')})")
                    video_info['tmdb_id'] = tmdb_info.get('id')
                    video_info['imdb_id'] = tmdb_info.get('imdb_id')
                    video_info['tmdb_title'] = tmdb_info.get('title')
                    video_info['tmdb_year'] = tmdb_info.get('year')
            except Exception as e:
                logger.warning(f"TMDB 搜索失败: {e}")

        # 并发搜索所有字幕源，每个源有独立的超时和熔断器
        tasks = []
        source_timeouts = {
            'subhd': 30,
            'assrt': 20,
            'opensubtitles': 15,
            'shooter': 10,
        }

        # 导入熔断器
        from backend.subtitle_sources import get_circuit_breaker, CircuitBreakerOpen

        for source_name in subtitle_sources:
            source = get_source(source_name)
            if not source:
                logger.warning(f"字幕源未找到: {source_name}")
                continue

            # 检查熔断器状态
            breaker = get_circuit_breaker(source_name)
            if breaker.is_open:
                logger.info(f"字幕源 {source_name} 熔断器已断开，跳过搜索")
                continue

            logger.info(f"使用字幕源: {source_name} (熔断器状态: {breaker._state})")

            async def search_with_circuit_break(source_name: str, source_obj):
                """带熔断器保护的搜索"""
                breaker = get_circuit_breaker(source_name)
                try:
                    if not await breaker.can_proceed():
                        raise CircuitBreakerOpen(f"字幕源 {source_name} 熔断器已断开")
                    result = await source_obj.search(video_info)
                    breaker.record_success()
                    return result
                except CircuitBreakerOpen:
                    raise
                except asyncio.TimeoutError:
                    breaker.record_failure()
                    raise
                except Exception as e:
                    breaker.record_failure()
                    raise

            # 包装搜索函数，添加超时
            timeout = source_timeouts.get(source_name.lower(), 15)
            try:
                task = asyncio.create_task(
                    asyncio.wait_for(
                        search_with_circuit_break(source_name, source),
                        timeout=timeout
                    )
                )
                tasks.append((source_name, task))
            except Exception as e:
                logger.error(f"创建字幕源 {source_name} 搜索任务失败: {e}")

        if tasks:
            results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
            for (source_name, _), result in zip(tasks, results):
                if isinstance(result, list):
                    all_results.extend(result)
                    logger.info(f"字幕源 {source_name} 返回 {len(result)} 个结果")
                elif isinstance(result, asyncio.TimeoutError):
                    logger.warning(f"字幕源 {source_name} 搜索超时")
                elif isinstance(result, CircuitBreakerOpen):
                    logger.warning(f"字幕源 {source_name} 熔断器已断开: {result}")
                elif isinstance(result, Exception):
                    logger.error(f"搜索字幕源 {source_name} 异常: {result}")

        # 过滤非中文字幕
        chinese_results = [
            r for r in all_results
            if r.language.lower() in ['zh', 'zh-cn', 'zh-tw', 'zh-hk', 'chi', 'chs', 'cht', 'cn']
        ]

        logger.info(f"找到 {len(chinese_results)} 个中文字幕")
        reranked_results = self._rerank_subtitle_results(chinese_results, video_info)
        logger.info(f"Matched {len(reranked_results)} Chinese subtitles after reranking")
        return reranked_results
    
    def _record_failure(self, file_hash: str):
        """记录失败次数"""
        self.failed_files[file_hash] = self.failed_files.get(file_hash, 0) + 1
        logger.debug(f"记录失败: {file_hash}, 当前失败次数: {self.failed_files[file_hash]}")
    
    async def process_single_file(self, video_path: str) -> bool:
        """处理单个文件（用于手动触发）"""
        if not os.path.exists(video_path):
            logger.error(f"文件不存在: {video_path}")
            return False
        
        # 重置处理状态
        file_hash = self._get_file_hash(video_path)
        if file_hash in self.processed_files:
            self.processed_files.remove(file_hash)
        if file_hash in self.failed_files:
            del self.failed_files[file_hash]
        
        return await self._process_video(video_path)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        # 扫描电影和电视剧
        movies = self.get_movies()
        tvshows = self.get_tvshows()
        
        # 计算电影统计
        movies_with_subtitle = sum(1 for m in movies if m.get('hasSubtitle', False))
        
        # 计算电视剧统计
        total_episodes = 0
        episodes_with_subtitle = 0
        for show in tvshows:
            for season in show.get('seasons', []):
                for episode in season.get('episodes', []):
                    total_episodes += 1
                    if episode.get('hasSubtitle', False):
                        episodes_with_subtitle += 1
        
        return {
            'totalMovies': len(movies),
            'moviesWithSubtitle': movies_with_subtitle,
            'moviesWithoutSubtitle': len(movies) - movies_with_subtitle,
            'totalTVShows': len(tvshows),
            'totalEpisodes': total_episodes,
            'episodesWithSubtitle': episodes_with_subtitle,
            'episodesWithoutSubtitle': total_episodes - episodes_with_subtitle,
            'recentDownloads': len([f for f in self.processed_files if f not in self.failed_files]),
            'pendingTasks': len(self.failed_files)
        }

    def _stable_int_id(self, value: str) -> int:
        """Create a stable positive integer id from a string."""
        return int(hashlib.md5(value.encode()).hexdigest(), 16) % 10000000

    def _extract_series_name(self, filename: str) -> str:
        """Extract a series title from an episode filename."""
        name_without_ext = os.path.splitext(filename)[0]
        name_without_ext = re.sub(r'^[\[\(\{].*?[\]\)\}]\s*', '', name_without_ext)
        show_name = re.sub(r'[.\s_-]*[Ss]\d{1,2}[Ee]\d{1,2}.*$', '', name_without_ext)
        return show_name.replace('.', ' ').replace('_', ' ').strip()

    def _build_subtitle_stats(self, with_subtitle: int, total: int) -> dict:
        """Return subtitle stats in both current and legacy field names."""
        missing = total - with_subtitle
        return {
            'withSubtitle': with_subtitle,
            'withoutSubtitle': missing,
            'has': with_subtitle,
            'missing': missing,
        }

    def _get_cached_library(self, cache_key: str):
        entry = self._library_cache.get(cache_key)
        if not entry:
            return None
        if entry["data"] is None or time.time() >= entry["expires_at"]:
            return None

        # 检查 NFO 文件是否有更新（基于 mtime 判断缓存是否失效）
        cached_nfo_mtimes = entry.get("nfo_mtimes", {})
        if cached_nfo_mtimes:
            current_mtimes = self._scan_nfo_mtimes(cache_key)
            if current_mtimes != cached_nfo_mtimes:
                logger.info(f"NFO 文件已变化，刷新缓存: {cache_key}")
                self._invalidate_library_cache(cache_key)
                return None

        logger.debug(f"Using cached library view: {cache_key}")
        return entry["data"]

    def _scan_nfo_mtimes(self, cache_key: str) -> Dict[str, float]:
        """
        扫描指定媒体类型目录下的所有 NFO 文件及其 mtime
        用于检测文件是否发生变化
        """
        nfo_mtimes = {}
        dir_map = {
            "movies": config.MOVIE_DIR,
            "tvshows": config.TV_DIR,
            "anime": config.ANIME_DIR,
        }
        base_dir = dir_map.get(cache_key)
        if not base_dir or not os.path.exists(base_dir):
            return nfo_mtimes

        for root, _, files in os.walk(base_dir):
            for fname in files:
                if fname.lower().endswith(('.nfo', '.NFO')):
                    fpath = os.path.join(root, fname)
                    try:
                        nfo_mtimes[fpath] = os.path.getmtime(fpath)
                    except OSError:
                        pass
        return nfo_mtimes

    def _set_cached_library(self, cache_key: str, data: list):
        # 同时记录扫描时的 NFO 文件 mtimes
        nfo_mtimes = self._scan_nfo_mtimes(cache_key)
        self._library_cache[cache_key] = {
            "expires_at": time.time() + self._library_cache_ttl,
            "data": data,
            "nfo_mtimes": nfo_mtimes,
        }

    def _invalidate_library_cache(self, *cache_keys: str):
        keys = cache_keys or tuple(self._library_cache.keys())
        for cache_key in keys:
            if cache_key in self._library_cache:
                self._library_cache[cache_key] = {"expires_at": 0.0, "data": None}

    def _cache_key_for_video_path(self, video_path: str) -> Optional[str]:
        normalized = video_path.replace("\\", "/")
        candidates = (
            ("movies", config.MOVIE_DIR),
            ("tvshows", config.TV_DIR),
            ("anime", config.ANIME_DIR),
        )
        for cache_key, base_dir in candidates:
            if base_dir and normalized.startswith(base_dir.replace("\\", "/")):
                return cache_key
        return None

    def _mark_cached_video_has_subtitle(self, video_path: str, has_subtitle: bool):
        cache_key = self._cache_key_for_video_path(video_path)
        if not cache_key:
            return

        cached = self._get_cached_library(cache_key)
        if not cached:
            return

        if cache_key == "movies":
            for movie in cached:
                if movie.get("path") == video_path:
                    movie["hasSubtitle"] = has_subtitle
                    return
            return

        for show in cached:
            total_episodes = 0
            episodes_with_subtitle = 0
            updated = False
            for season in show.get("seasons", []):
                for episode in season.get("episodes", []):
                    if episode.get("path") == video_path:
                        episode["hasSubtitle"] = has_subtitle
                        updated = True
                    total_episodes += 1
                    if episode.get("hasSubtitle"):
                        episodes_with_subtitle += 1
            if updated:
                show["subtitleStats"] = self._build_subtitle_stats(episodes_with_subtitle, total_episodes)
                return

    def _subtitle_format_bonus(self, result: SubtitleResult) -> float:
        """根据字幕格式返回匹配加分，使用可配置的格式权重"""
        format_name = (getattr(result, "file_format", "") or "").lower().lstrip(".")
        # 从配置中获取格式加分，默认返回 0.0
        return self._subtitle_format_bonus_config.get(format_name, 0.0)

    def _subtitle_result_key(self, result: SubtitleResult) -> tuple:
        """Build a stable dedupe key for subtitle results."""
        title_key = normalize_release_text(result.title or result.filename or "")
        if result.source.lower() == "subhd":
            summary_key = normalize_release_text(getattr(result, "summary", "") or " ".join(getattr(result, "meta_tags", []) or []))
            format_key = normalize_release_text(getattr(result, "file_format", ""))
            return (
                result.source.lower(),
                title_key,
                summary_key,
                format_key,
            )
        return (
            result.source.lower(),
            getattr(result, "download_url", "") or title_key,
            title_key,
        )

    def _rerank_subtitle_results(self, results: List[SubtitleResult], video_info: dict) -> List[SubtitleResult]:
        """Apply a shared reranker so scores are comparable across sources."""
        reranked: Dict[tuple, SubtitleResult] = {}

        for result in results:
            title = result.title or result.filename or ""
            final_score = score_release_title(
                title,
                video_info,
                source_name=result.source,
                source_score=result.score,
            )
            final_score += self._subtitle_format_bonus(result)
            final_score = max(0.0, min(final_score, 1.0))
            result.score = final_score

            result_key = self._subtitle_result_key(result)
            existing = reranked.get(result_key)
            if existing is None or final_score > existing.score:
                reranked[result_key] = result

        sorted_results = sorted(
            reranked.values(),
            key=lambda item: item.score,
            reverse=True,
        )

        if video_info.get('season') and video_info.get('episode'):
            before_filter = len(sorted_results)
            sorted_results = [item for item in sorted_results if item.score >= 0.35]
            if before_filter != len(sorted_results):
                logger.info(f"TV episodic rerank filter removed {before_filter - len(sorted_results)} weak subtitle matches")

        if video_info.get('season') and video_info.get('episode') and sorted_results:
            target_token = f"s{int(video_info['season']):02d}e{int(video_info['episode']):02d}"
            exact_results = [
                item for item in sorted_results
                if target_token in normalize_release_text((item.title or item.filename or '')).replace(' ', '')
            ]
            if exact_results:
                fallback_results = [item for item in sorted_results if item not in exact_results][:5]
                sorted_results = exact_results + fallback_results
                logger.info(f"TV episodic exact-match prioritization kept {len(exact_results)} exact candidates for {target_token}")

        if sorted_results:
            top_preview = ", ".join(
                f"{item.source}:{item.title[:40]} ({item.score:.2f})"
                for item in sorted_results[:5]
            )
            logger.info(f"Top reranked subtitles: {top_preview}")

        return sorted_results

    def _find_episode_by_id(self, shows: list, episode_id: str):
        """Find a TV episode by the current id or the legacy composite id."""
        target_id = str(episode_id)

        for show in shows:
            for season in show.get('seasons', []):
                season_number = season.get('number')
                for episode in season.get('episodes', []):
                    if str(episode.get('id')) == target_id:
                        return episode

                    episode_number = episode.get('episodeNumber', episode.get('number'))
                    legacy_id = f"{show.get('id')}_{season_number}_{episode_number}"
                    if legacy_id == target_id:
                        return episode

        return None

    def _collect_video_subtitles(self, video_path: str) -> list:
        """List subtitle files beside a video file."""
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.smi', '.sami', '.sub', '.idx', '.sup']
        subtitles = []

        for file in os.listdir(video_dir):
            file_lower = file.lower()
            if not any(file_lower.endswith(ext) for ext in subtitle_extensions):
                continue

            file_stem = os.path.splitext(file)[0]
            if not (file_stem.startswith(video_name) or file_stem == video_name):
                continue

            file_path = os.path.join(video_dir, file)
            file_stat = os.stat(file_path)
            subtitles.append({
                "id": hashlib.md5(file_path.encode()).hexdigest()[:8],
                "filename": file,
                "path": file_path,
                "language": self._parse_subtitle_language(file),
                "format": os.path.splitext(file)[1][1:].upper(),
                "size": file_stat.st_size,
                "sizeFormatted": self._format_file_size(file_stat.st_size),
                "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            })

        return subtitles

    def _get_subtitle_candidates(self, video_path: str) -> list:
        """Return subtitle file paths that belong to a video file."""
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.smi', '.sami', '.sub', '.idx', '.sup']
        candidates = []

        for file in os.listdir(video_dir):
            file_lower = file.lower()
            if not any(file_lower.endswith(ext) for ext in subtitle_extensions):
                continue

            file_stem = os.path.splitext(file)[0]
            if file_stem.startswith(video_name) or file_stem == video_name:
                candidates.append(os.path.join(video_dir, file))

        return candidates

    def _resolve_downloaded_subtitle_path(
        self,
        download_result: bool | str,
        video_path: str,
        requested_path: str,
        before_paths: set,
    ) -> Optional[str]:
        """Resolve the actual subtitle file saved by a source download."""
        if isinstance(download_result, str) and os.path.exists(download_result):
            return download_result

        after_paths = set(self._get_subtitle_candidates(video_path))
        created_paths = sorted(after_paths - before_paths)
        if created_paths:
            return created_paths[0]

        if os.path.exists(requested_path):
            return requested_path
        return None

    def _backup_existing_file(self, file_path: str) -> Optional[str]:
        """Create a timestamped backup before overwriting a subtitle file."""
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        base_path, extension = os.path.splitext(file_path)
        backup_path = f"{base_path}.bak.{timestamp}{extension}"
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backed up subtitle: {file_path} -> {backup_path}")
        return backup_path

    def _decode_subtitle_bytes(self, content: bytes) -> str:
        """
        Decode subtitle bytes with a best-effort charset detection strategy.
        
        增强的中文编码检测：
        1. 先尝试 chardet 检测结果
        2. 对于中文文件，优先尝试 GB2312/GBK（很多字幕用这个编码但被 chardet 误判为 GB18030）
        3. 使用 UTF-8 系列兜底
        """
        detection = chardet.detect(content or b"")
        candidates = []

        detected_encoding = detection.get("encoding")
        if detected_encoding:
            detected_lower = detected_encoding.lower()
            # chardet 有时会误判，先保存原始检测结果
            candidates.append(detected_encoding)
            # 如果检测到是中文相关编码，额外添加更具体的编码尝试
            if detected_lower in ("gb18030", "gb2312", "gbk", "gb_2312", "gb_2312-80"):
                candidates.insert(0, "gbk")  # GBK 兼容性更好
                candidates.insert(0, "gb2312")

        candidates.extend([
            "utf-8-sig",
            "utf-8",
            "utf-16",
            "utf-16-le",
            "utf-16-be",
            "gbk",  # 提前 gbk 尝试
            "gb18030",
            "big5",
            "cp1252",
            "latin-1",
        ])

        tried = set()
        for encoding in candidates:
            normalized = encoding.lower()
            if normalized in tried:
                continue
            tried.add(normalized)
            try:
                decoded = content.decode(encoding)
                # 验证解码结果是否包含合理的中文字符密度
                if self._validate_decoded_content(decoded):
                    return decoded
            except Exception:
                continue

        return content.decode("utf-8", errors="replace")

    def _validate_decoded_content(self, text: str) -> bool:
        """
        验证解码后的字幕内容是否有效
        检查中文字符密度，防止乱码字幕被误认为有效
        """
        if not text:
            return False

        # 提取所有字符
        chars = list(text)
        if len(chars) == 0:
            return False

        # 统计中文字符数量
        chinese_chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text)
        chinese_ratio = len(chinese_chars) / len(chars)

        # 统计乱码特征（控制字符、非法 Unicode 代理对等）
        illegal_sequences = re.findall(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\uDC00-\uDFFF]', text)
        illegal_ratio = len(illegal_sequences) / len(chars)

        # 验证条件：
        # 1. 中文字符比例在合理范围（1% - 50%）
        # 2. 乱码字符比例低于 5%
        if chinese_ratio > 0.01 and chinese_ratio < 0.50 and illegal_ratio < 0.05:
            return True

        # 如果没有中文字符，至少确保不是乱码（乱码比例很低）
        if chinese_ratio <= 0.01 and illegal_ratio < 0.01:
            return True

        return False

    def _validate_subtitle_quality(self, subtitle_path: str) -> Dict[str, Any]:
        """
        验证字幕文件内容质量
        返回: {"valid": bool, "chinese_ratio": float, "line_count": int, "warnings": list}
        """
        warnings = []
        try:
            with open(subtitle_path, 'rb') as f:
                raw_content = f.read()

            text = self._decode_subtitle_bytes(raw_content)
            lines = [l.strip() for l in text.splitlines() if l.strip()]

            # 统计
            total_chars = len(text)
            chinese_chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', text)
            chinese_ratio = len(chinese_chars) / max(total_chars, 1)

            # 检查时间戳格式是否正确
            timestamp_errors = 0
            for line in lines:
                if '-->' in line:
                    parts = line.split('-->')
                    if len(parts) == 2:
                        try:
                            # 简单验证时间戳格式
                            start = parts[0].strip()
                            end = parts[1].strip()
                            if not re.match(r'\d{1,2}:\d{2}:\d{2}[,\.]\d{1,3}', start):
                                timestamp_errors += 1
                        except:
                            timestamp_errors += 1

            # 生成警告
            if chinese_ratio < 0.01:
                warnings.append("字幕中中文字符过少，可能不是正确的中文字幕")
            if timestamp_errors > len(lines) * 0.3:
                warnings.append("字幕时间戳格式错误较多")
            if len(lines) < 10:
                warnings.append("字幕行数过少，可能不完整")

            return {
                "valid": len(warnings) == 0,
                "chinese_ratio": round(chinese_ratio, 4),
                "line_count": len(lines),
                "warnings": warnings
            }
        except Exception as e:
            return {
                "valid": False,
                "chinese_ratio": 0.0,
                "line_count": 0,
                "warnings": [f"无法读取字幕文件: {e}"]
            }

    def _clean_subtitle_text(self, text: str) -> str:
        """Remove formatting markup while keeping human-readable line breaks."""
        normalized = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
        normalized = re.sub(r"\{\\.*?\}", "", normalized)
        normalized = re.sub(r"<[^>]+>", "", normalized)
        normalized = normalized.replace("\\N", "\n").replace("\\n", "\n").replace("|", "\n")
        normalized = unescape(normalized)
        lines = [line.strip() for line in normalized.splitlines()]
        cleaned = "\n".join(line for line in lines if line)
        return cleaned.strip()

    def _format_srt_timestamp(self, milliseconds: int) -> str:
        """Format milliseconds as an SRT timestamp."""
        total_ms = max(0, int(milliseconds))
        hours, remainder = divmod(total_ms, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        seconds, millis = divmod(remainder, 1_000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

    def _timestamp_to_milliseconds(self, value: str) -> Optional[int]:
        """Parse subtitle timestamps such as 00:01:02,345 or 00:01:02.345."""
        if not value:
            return None

        match = re.match(r"(?:(\d+):)?(\d{1,2}):(\d{2})[,.](\d{1,3})", value.strip())
        if not match:
            return None

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        fraction = match.group(4).ljust(3, "0")[:3]
        return ((hours * 60 + minutes) * 60 + seconds) * 1000 + int(fraction)

    def _ass_timestamp_to_milliseconds(self, value: str) -> Optional[int]:
        """Parse ASS timestamps such as 0:01:02.34."""
        match = re.match(r"(\d+):(\d{1,2}):(\d{2})\.(\d{1,2})", value.strip())
        if not match:
            return None

        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        centiseconds = int(match.group(4).ljust(2, "0")[:2])
        return ((hours * 60 + minutes) * 60 + seconds) * 1000 + centiseconds * 10

    def _srt_entries_to_text(self, entries: List[Dict[str, Any]]) -> str:
        """Serialize normalized subtitle entries back to UTF-8 SRT text."""
        blocks = []
        for index, entry in enumerate(entries, start=1):
            text = (entry.get("text") or "").strip()
            start = entry.get("start")
            end = entry.get("end")
            if not text or start is None or end is None or end <= start:
                continue

            blocks.append(
                f"{index}\n"
                f"{self._format_srt_timestamp(start)} --> {self._format_srt_timestamp(end)}\n"
                f"{text}\n"
            )

        return "\n".join(blocks).strip() + ("\n" if blocks else "")

    def _normalize_srt_text(self, text: str) -> Optional[str]:
        """Normalize existing SRT text to UTF-8 with LF line endings."""
        pattern = re.compile(
            r"(?:^\s*\d+\s*\n)?"
            r"\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}[,.]\d{1,3})\s*\n"
            r"(.*?)(?=\n{2,}(?:\d+\s*\n)?\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->|$)",
            re.S | re.M,
        )
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        entries = []
        for match in pattern.finditer(normalized):
            start = self._timestamp_to_milliseconds(match.group(1))
            end = self._timestamp_to_milliseconds(match.group(2))
            body = self._clean_subtitle_text(match.group(3))
            if start is None or end is None or not body:
                continue
            entries.append({"start": start, "end": end, "text": body})

        if entries:
            return self._srt_entries_to_text(entries)

        if "-->" in normalized:
            return normalized + "\n"
        return None

    def _convert_vtt_to_srt(self, text: str) -> Optional[str]:
        """Convert WEBVTT subtitles to SRT."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = []
        for line in normalized.split("\n"):
            stripped = line.strip()
            if stripped == "WEBVTT" or stripped.startswith("NOTE") or stripped.startswith("STYLE"):
                continue
            lines.append(line)
        return self._normalize_srt_text("\n".join(lines).replace(".", ","))

    def _convert_ass_to_srt(self, text: str) -> Optional[str]:
        """Convert ASS/SSA subtitles to plain SRT."""
        format_fields: List[str] = []
        entries: List[Dict[str, Any]] = []

        for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("Format:"):
                format_fields = [field.strip().lower() for field in line.split(":", 1)[1].split(",")]
                continue
            if not line.startswith("Dialogue:") or not format_fields:
                continue

            payload = line.split(":", 1)[1].lstrip()
            parts = payload.split(",", len(format_fields) - 1)
            if len(parts) != len(format_fields):
                continue

            values = dict(zip(format_fields, parts))
            start = self._ass_timestamp_to_milliseconds(values.get("start", ""))
            end = self._ass_timestamp_to_milliseconds(values.get("end", ""))
            body = self._clean_subtitle_text(values.get("text", ""))
            if start is None or end is None or not body:
                continue
            entries.append({"start": start, "end": end, "text": body})

        return self._srt_entries_to_text(entries) if entries else None

    def _convert_smi_to_srt(self, text: str) -> Optional[str]:
        """Convert SAMI/SMI subtitles to plain SRT."""
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        pattern = re.compile(
            r"<sync[^>]*start\s*=\s*(\d+)[^>]*>(.*?)(?=<sync[^>]*start\s*=|\Z)",
            re.I | re.S,
        )
        matches = list(pattern.finditer(normalized))
        entries: List[Dict[str, Any]] = []

        for index, match in enumerate(matches):
            start = int(match.group(1))
            body = self._clean_subtitle_text(match.group(2))
            if not body:
                continue

            if index + 1 < len(matches):
                end = int(matches[index + 1].group(1))
            else:
                end = start + 3000

            if end <= start:
                end = start + 3000
            entries.append({"start": start, "end": end, "text": body})

        return self._srt_entries_to_text(entries) if entries else None

    def _convert_subtitle_text_to_srt(self, subtitle_path: str) -> Optional[str]:
        """Convert a text subtitle file to normalized UTF-8 SRT content."""
        with open(subtitle_path, "rb") as file_obj:
            raw_content = file_obj.read()

        suffix = os.path.splitext(subtitle_path)[1].lower()
        text = self._decode_subtitle_bytes(raw_content)

        if suffix == ".srt":
            return self._normalize_srt_text(text)
        if suffix in {".ass", ".ssa"}:
            return self._convert_ass_to_srt(text)
        if suffix == ".vtt":
            return self._convert_vtt_to_srt(text)
        if suffix in {".smi", ".sami"}:
            return self._convert_smi_to_srt(text)

        return None

    def _replace_subtitle_file(self, source_path: str, target_path: str) -> str:
        """Move a subtitle file into place, backing up the old target when configured."""
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if settings.BACKUP_EXISTING_SUBTITLE:
            self._backup_existing_file(target_path)
        elif os.path.exists(target_path) and os.path.normcase(source_path) != os.path.normcase(target_path):
            os.remove(target_path)

        if os.path.normcase(source_path) != os.path.normcase(target_path):
            shutil.move(source_path, target_path)
        return target_path

    def _normalize_non_text_subtitle(self, video_path: str, subtitle_path: str) -> Dict[str, Any]:
        """Rename image-based subtitles to Plex-compatible sidecar names."""
        suffix = os.path.splitext(subtitle_path)[1].lower()
        target_path = os.path.splitext(
            get_subtitle_save_path(video_path, lang_code="zh-cn", plex_format=settings.PLEX_NAMING_FORMAT)
        )[0] + suffix
        final_path = self._replace_subtitle_file(subtitle_path, target_path)
        return {
            "path": final_path,
            "converted": False,
            "warning": f"当前字幕格式 {suffix} 无法转换为 UTF-8 SRT，已按 Plex 命名保留原格式",
        }

    def _extract_7z_subtitle(self, archive_path: str) -> str | None:
        """Extract the best subtitle member from a local 7z archive."""
        try:
            import py7zr
            from backend.subtitle_sources import SubHDSource

            helper = SubHDSource()
            with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                member_name = helper._pick_archive_member(archive.getnames())
                if not member_name:
                    logger.warning("7z archive does not contain a supported subtitle file")
                    return None
                extracted = archive.read([member_name])
                member_data = extracted.get(member_name)
                if member_data is None:
                    logger.warning(f"7z archive member missing after extraction: {member_name}")
                    return None
                member_bytes = member_data.read() if hasattr(member_data, "read") else member_data
                extension = os.path.splitext(member_name)[1] or ".srt"
                target_path = os.path.splitext(archive_path)[0] + extension
                with open(target_path, "wb") as file_obj:
                    file_obj.write(member_bytes)
                logger.info(f"Subtitle extracted from local 7z: {target_path}")
                return target_path
        except Exception as exc:
            logger.error(f"Failed to extract local 7z subtitle: {exc}")
            return None

    def _normalize_downloaded_subtitle(self, video_path: str, subtitle_path: str) -> Dict[str, Any]:
        """Standardize downloaded subtitles for Plex consumption."""
        suffix = os.path.splitext(subtitle_path)[1].lower()
        target_srt_path = get_subtitle_save_path(
            video_path,
            lang_code="zh-cn",
            plex_format=settings.PLEX_NAMING_FORMAT,
        )

        if suffix == ".7z":
            extracted_path = self._extract_7z_subtitle(subtitle_path)
            if not extracted_path:
                return {
                    "path": subtitle_path,
                    "converted": False,
                    "warning": "7z 字幕包解压失败，已保留原文件",
                }
            if os.path.exists(subtitle_path) and os.path.normcase(extracted_path) != os.path.normcase(subtitle_path):
                os.remove(subtitle_path)
            subtitle_path = extracted_path
            suffix = os.path.splitext(subtitle_path)[1].lower()

        if suffix in {".sup", ".idx", ".sub"}:
            return self._normalize_non_text_subtitle(video_path, subtitle_path)

        srt_text = self._convert_subtitle_text_to_srt(subtitle_path)
        if srt_text is None:
            if suffix == ".srt":
                final_path = self._replace_subtitle_file(subtitle_path, target_srt_path)
                return {"path": final_path, "converted": False}
            return self._normalize_non_text_subtitle(video_path, subtitle_path)

        if settings.BACKUP_EXISTING_SUBTITLE:
            self._backup_existing_file(target_srt_path)
        elif os.path.exists(target_srt_path) and os.path.normcase(subtitle_path) != os.path.normcase(target_srt_path):
            os.remove(target_srt_path)

        with open(target_srt_path, "w", encoding="utf-8", newline="\n") as file_obj:
            file_obj.write(srt_text)

        if os.path.exists(subtitle_path) and os.path.normcase(subtitle_path) != os.path.normcase(target_srt_path):
            os.remove(subtitle_path)

        logger.info(f"Subtitle normalized to UTF-8 SRT: {target_srt_path}")
        return {"path": target_srt_path, "converted": True}

    def _parse_plex_path_mappings(self) -> List[tuple[str, str]]:
        """Parse Plex path mappings from a newline-delimited from=to list."""
        raw_value = settings.PLEX_PATH_MAPPINGS or ""
        mappings = []
        for raw_line in raw_value.splitlines():
            line = raw_line.strip()
            if not line or "=" not in line:
                continue
            source_prefix, target_prefix = [part.strip() for part in line.split("=", 1)]
            if source_prefix and target_prefix:
                mappings.append((source_prefix.replace("\\", "/"), target_prefix.replace("\\", "/")))
        mappings.sort(key=lambda item: len(item[0]), reverse=True)
        return mappings

    def _map_path_for_plex(self, path: str) -> str:
        """Translate local managed paths to Plex-visible paths."""
        normalized_path = path.replace("\\", "/")
        for source_prefix, target_prefix in self._parse_plex_path_mappings():
            if normalized_path.startswith(source_prefix):
                return normalized_path.replace(source_prefix, target_prefix, 1)
        return normalized_path

    async def _load_plex_sections(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Fetch Plex library sections and their root locations."""
        server_url = settings.PLEX_SERVER_URL.rstrip("/")
        token = settings.PLEX_TOKEN
        sections_url = f"{server_url}/library/sections?X-Plex-Token={quote(token)}"

        async with session.get(sections_url, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"Plex sections request failed: {response.status}")
            payload = await response.text()

        root = ET.fromstring(payload)
        sections = []
        for directory in root.findall(".//Directory"):
            section_id = directory.attrib.get("key")
            section_type = directory.attrib.get("type")
            locations = [
                location.attrib.get("path", "").replace("\\", "/")
                for location in directory.findall("./Location")
                if location.attrib.get("path")
            ]
            if section_id and locations:
                sections.append({"id": section_id, "type": section_type, "locations": locations})
        return sections

    def _match_plex_section(self, plex_path: str, sections: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Match a media file to the most specific Plex library section."""
        best_match = None
        best_length = -1
        for section in sections:
            for location in section["locations"]:
                if plex_path.startswith(location) and len(location) > best_length:
                    best_match = section
                    best_length = len(location)
        return best_match

    async def _find_plex_rating_key(
        self,
        session: aiohttp.ClientSession,
        section: Dict[str, Any],
        plex_path: str,
    ) -> Optional[str]:
        """Find the Plex metadata ratingKey for the current media file."""
        server_url = settings.PLEX_SERVER_URL.rstrip("/")
        token = settings.PLEX_TOKEN
        endpoint = "allLeaves" if section.get("type") in {"show", "artist"} else "all"
        url = f"{server_url}/library/sections/{section['id']}/{endpoint}?X-Plex-Token={quote(token)}"

        async with session.get(url, timeout=30) as response:
            if response.status != 200:
                logger.warning(f"Plex metadata listing failed: {response.status}")
                return None
            payload = await response.text()

        root = ET.fromstring(payload)
        normalized_target = plex_path.replace("\\", "/")
        for video in root.findall(".//Video"):
            rating_key = video.attrib.get("ratingKey")
            if not rating_key:
                continue
            for part in video.findall(".//Part"):
                part_path = part.attrib.get("file", "").replace("\\", "/")
                if part_path == normalized_target:
                    return rating_key
        return None

    async def _refresh_plex_media(self, video_path: str) -> Dict[str, Any]:
        """Refresh Plex after a subtitle download so the new sidecar becomes selectable."""
        if not settings.PLEX_REFRESH_AFTER_DOWNLOAD:
            return {"attempted": False, "refreshed": False, "message": "Plex refresh disabled"}

        if not settings.PLEX_SERVER_URL or not settings.PLEX_TOKEN:
            return {"attempted": False, "refreshed": False, "message": "Plex server URL or token missing"}

        try:
            plex_video_path = self._map_path_for_plex(video_path)
            plex_video_dir = os.path.dirname(plex_video_path).replace("\\", "/")
            headers = {"Accept": "application/xml"}

            async with aiohttp.ClientSession(headers=headers) as session:
                sections = await self._load_plex_sections(session)
                section = self._match_plex_section(plex_video_path, sections)
                if not section:
                    return {
                        "attempted": True,
                        "refreshed": False,
                        "message": "No matching Plex library section for media path",
                    }

                server_url = settings.PLEX_SERVER_URL.rstrip("/")
                token = quote(settings.PLEX_TOKEN)
                refresh_url = (
                    f"{server_url}/library/sections/{section['id']}/refresh"
                    f"?path={quote(plex_video_dir, safe='/')}&X-Plex-Token={token}"
                )
                async with session.get(refresh_url, timeout=20) as response:
                    if response.status not in {200, 204}:
                        logger.warning(f"Plex partial scan request failed: {response.status}")

                rating_key = await self._find_plex_rating_key(session, section, plex_video_path)
                if not rating_key:
                    return {
                        "attempted": True,
                        "refreshed": True,
                        "message": "Triggered Plex partial scan for media directory",
                    }

                metadata_url = f"{server_url}/library/metadata/{rating_key}/refresh?X-Plex-Token={token}"
                async with session.put(metadata_url, timeout=20) as response:
                    if response.status not in {200, 204}:
                        return {
                            "attempted": True,
                            "refreshed": False,
                            "message": f"Plex item refresh failed: HTTP {response.status}",
                        }

                return {
                    "attempted": True,
                    "refreshed": True,
                    "message": "Triggered Plex item refresh",
                    "ratingKey": rating_key,
                }
        except Exception as exc:
            logger.warning(f"Plex refresh failed: {exc}")
            return {"attempted": True, "refreshed": False, "message": str(exc)}

    async def _download_subtitle_for_video(
        self,
        video_path: str,
        subtitle_id: str,
        source_name: str = None,
        subtitle_result: dict = None
    ) -> dict:
        """Download a subtitle to the video's directory."""
        if not source_name:
            return {"success": False, "message": "未指定字幕源"}

        source = get_source(source_name)
        if not source:
            return {"success": False, "message": "字幕源不存在"}

        subtitle_path = get_subtitle_save_path(
            video_path,
            lang_code="zh-cn",
            plex_format=settings.PLEX_NAMING_FORMAT
        )
        before_paths = set(self._get_subtitle_candidates(video_path))
        download_state: bool | str = False

        async def finalize_download() -> dict:
            actual_path = self._resolve_downloaded_subtitle_path(
                download_result=download_state,
                video_path=video_path,
                requested_path=subtitle_path,
                before_paths=before_paths,
            )
            if not actual_path:
                return {"success": False, "message": "字幕下载成功但未找到保存的字幕文件"}
            normalized = self._normalize_downloaded_subtitle(video_path, actual_path)
            plex_refresh = await self._refresh_plex_media(video_path)

            result = {
                "success": True,
                "message": "字幕下载成功",
                "path": normalized["path"],
                "convertedToSrt": normalized.get("converted", False),
                "plexRefresh": plex_refresh,
            }
            self._mark_cached_video_has_subtitle(video_path, True)
            if normalized.get("warning"):
                result["warning"] = normalized["warning"]
            return result

        if source_name.lower() == 'subhd' and subtitle_result:
            from backend.subtitle_sources import SubtitleResult as SourceSubtitleResult

            result = SourceSubtitleResult(
                id=subtitle_result['id'],
                source=subtitle_result['source'],
                title=subtitle_result['title'],
                language=subtitle_result['language'],
                download_url=subtitle_result['downloadUrl'],
                score=subtitle_result.get('score', 0),
                filename=subtitle_result.get('filename')
            )
            download_state = await source.download(result, subtitle_path)
            if download_state:
                return await finalize_download()
            return {"success": False, "message": "下载失败"}

        video_info = NFOParser.get_video_info_with_nfo(video_path)
        results = await source.search(video_info)
        for result in results:
            if str(result.id) != str(subtitle_id):
                continue

            download_state = await source.download(result, subtitle_path)
            if download_state:
                return await finalize_download()
            break

        return {"success": False, "message": "下载失败"}

    def _scan_series_library(self, base_dir: str, media_type: str) -> list:
        """Scan a TV or anime library and normalize the response shape."""
        shows = {}

        if not base_dir or not os.path.exists(base_dir):
            return []

        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if not is_tv_episode(file):
                    continue

                file_path = os.path.join(root, file)
                episode_info = extract_video_info(file_path)
                show_name = self._extract_series_name(file)
                if not show_name:
                    continue

                show_key = show_name.lower()
                poster_path = self._find_show_poster(root, show_name)

                if show_key not in shows:
                    shows[show_key] = {
                        'id': self._stable_int_id(f"{media_type}:{show_name}"),
                        'name': show_name,
                        'year': episode_info.get('year'),
                        'posterPath': poster_path,
                        'seasons': {}
                    }
                elif not shows[show_key].get('posterPath') and poster_path:
                    shows[show_key]['posterPath'] = poster_path

                season_num = episode_info.get('season', 1)
                if season_num not in shows[show_key]['seasons']:
                    shows[show_key]['seasons'][season_num] = {
                        'posterPath': self._find_season_poster(root, season_num),
                        'episodes': []
                    }

                shows[show_key]['seasons'][season_num]['episodes'].append({
                    'id': self._stable_int_id(f"{media_type}:episode:{file_path}"),
                    'episodeNumber': episode_info.get('episode', 0),
                    'filename': file,
                    'path': file_path,
                    'hasSubtitle': has_chinese_subtitle(file_path)
                })

        result = []
        for show_data in shows.values():
            total_episodes = 0
            episodes_with_subtitle = 0
            seasons_list = []

            for season_num in sorted(show_data['seasons'].keys()):
                season = show_data['seasons'][season_num]
                episodes = sorted(
                    season['episodes'],
                    key=lambda episode: (episode.get('episodeNumber', 0), episode.get('filename', ''))
                )

                total_episodes += len(episodes)
                episodes_with_subtitle += sum(1 for episode in episodes if episode['hasSubtitle'])

                seasons_list.append({
                    'number': season_num,
                    'posterPath': season.get('posterPath'),
                    'episodes': episodes
                })

            result.append({
                'id': show_data['id'],
                'name': show_data['name'],
                'year': show_data.get('year'),
                'posterPath': show_data.get('posterPath'),
                'seasonCount': len(seasons_list),
                'episodeCount': total_episodes,
                'subtitleStats': self._build_subtitle_stats(episodes_with_subtitle, total_episodes),
                'seasons': seasons_list
            })

        result.sort(key=lambda show: show['name'].lower())
        return result
    
    def get_movies(self) -> list:
        """获取电影列表"""
        cached = self._get_cached_library("movies")
        if cached is not None:
            return cached

        movies = []
        movie_dir = config.MOVIE_DIR

        if not movie_dir or not os.path.exists(movie_dir):
            return movies

        for root, dirs, files in os.walk(movie_dir):
                # 跳过电视剧目录
                if any(pattern in root.lower() for pattern in ['season', 's01', 's02', 'specials']):
                    continue

                for file in files:
                    if is_movie_file(file):
                        file_path = os.path.join(root, file)

                        # 使用 NFO 解析器获取视频信息（包含 NFO 文件信息）
                        video_info = NFOParser.get_video_info_with_nfo(file_path)

                        # 检查同目录下是否有海报图片
                        poster_path = None
                        poster_extensions = ['.jpg', '.jpeg', '.png', '.webp']
                        poster_names = ['poster', 'cover', 'folder', 'thumb', 'thumbnail']

                        for poster_name in poster_names:
                            for ext in poster_extensions:
                                potential_poster = os.path.join(root, f"{poster_name}{ext}")
                                if os.path.exists(potential_poster):
                                    poster_path = potential_poster
                                    break
                            if poster_path:
                                break

                        # 获取 NFO 中的标题
                        nfo_title = None
                        if video_info.get('nfo'):
                            nfo_title = video_info['nfo'].get('title')

                        # 使用稳定的 ID 生成方式（基于文件路径的哈希）
                        stable_id = self._stable_int_id(file_path)

                        movies.append({
                            'id': stable_id,
                            'name': nfo_title or video_info.get('title', os.path.splitext(file)[0]),
                            'filename': file,
                            'path': file_path,
                            'hasSubtitle': has_chinese_subtitle(file_path),
                            'year': video_info.get('year'),
                            'resolution': video_info.get('resolution'),
                            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                            'posterPath': poster_path,
                            'tmdbId': video_info.get('tmdb_id'),
                            'imdbId': video_info.get('imdb_id'),
                            'originalTitle': video_info.get('original_title'),
                            'nfoPath': video_info.get('nfo_path')
                        })

        self._set_cached_library("movies", movies)
        return movies
    
    def _find_show_poster(self, episode_dir: str, show_name: str) -> Optional[str]:
        """查找电视剧海报"""
        # 可能的父目录（剧集所在目录的父目录或当前目录）
        possible_dirs = [episode_dir]
        parent_dir = os.path.dirname(episode_dir)
        if parent_dir and parent_dir != episode_dir:
            possible_dirs.append(parent_dir)
        
        # 常见海报文件名
        poster_names = ['poster.jpg', 'poster.png', 'folder.jpg', 'folder.png', 
                       'show.jpg', 'show.png', f'{show_name}.jpg', f'{show_name}.png']
        
        for directory in possible_dirs:
            for poster_name in poster_names:
                poster_path = os.path.join(directory, poster_name)
                if os.path.exists(poster_path):
                    return poster_path
        
        return None
    
    def _find_season_poster(self, episode_dir: str, season_num: int) -> Optional[str]:
        """查找季海报"""
        # 可能的目录
        possible_dirs = [episode_dir]
        parent_dir = os.path.dirname(episode_dir)
        if parent_dir and parent_dir != episode_dir:
            possible_dirs.append(parent_dir)
        
        # 常见季海报文件名
        season_poster_names = [
            f'season{season_num:02d}-poster.jpg', f'season{season_num:02d}-poster.png',
            f'season{season_num}-poster.jpg', f'season{season_num}-poster.png',
            f'Season {season_num}.jpg', f'Season {season_num}.png',
            f'season{season_num:02d}.jpg', f'season{season_num:02d}.png',
            'season-poster.jpg', 'season-poster.png'
        ]
        
        for directory in possible_dirs:
            for poster_name in season_poster_names:
                poster_path = os.path.join(directory, poster_name)
                if os.path.exists(poster_path):
                    return poster_path
        
        return None
    
    def scan_library(self, background: bool = False):
        """
        扫描媒体库（供API调用）

        Args:
            background: 是否在后台异步执行，默认 False（同步执行便于 API 返回）
        """
        logger.info(f"开始扫描媒体库... (background={background})")
        try:
            self._invalidate_library_cache()

            # 创建扫描任务
            task_id = self._generate_task_id()
            scan_task_info = {
                "id": task_id,
                "type": "scan",
                "status": "running",
                "createdAt": datetime.now().isoformat(),
                "progress": 0,
                "message": "扫描中..."
            }
            self._task_queue.append(scan_task_info)
            self._save_task_queue()

            if background:
                # 后台执行
                async def run_background_scan():
                    try:
                        await self.scan_and_process()
                        self._update_task_status(task_id, "completed", 100, "扫描完成")
                    except Exception as e:
                        logger.error(f"后台扫描失败: {e}")
                        self._update_task_status(task_id, "failed", 0, f"扫描失败: {e}")

                # 启动后台任务
                asyncio.create_task(run_background_scan())
                return {"success": True, "message": "扫描任务已启动", "taskId": task_id}
            else:
                # 同步执行
                asyncio.run(self.scan_and_process())
                self._update_task_status(task_id, "completed", 100, "扫描完成")
                logger.info("媒体库扫描完成")
                return {"success": True, "message": "扫描完成"}
        except Exception as e:
            logger.error(f"扫描媒体库失败: {e}")
            return {"success": False, "message": str(e)}

    def _update_task_status(self, task_id: str, status: str, progress: int, message: str):
        """更新任务状态"""
        for task in self._task_queue:
            if task.get('id') == task_id:
                task['status'] = status
                task['progress'] = progress
                task['message'] = message
                task['updatedAt'] = datetime.now().isoformat()
                break
        self._save_task_queue()
        # 更新扫描进度
        self._scan_progress["isScanning"] = (status == "running")
        self._scan_progress["progress"] = progress

    def get_scan_status(self):
        """获取扫描状态"""
        return {
            "isScanning": self._scan_progress.get("isScanning", False),
            "progress": self._scan_progress.get("progress", 100),
            "currentFile": self._scan_progress.get("currentFile", ""),
            "totalFiles": self._scan_progress.get("totalFiles", 0),
            "processedFiles": len(self.processed_files)
        }

    def get_tasks(self):
        """获取任务队列"""
        return self._task_queue[-20:]  # 返回最近20个任务

    def cancel_task(self, task_id: str):
        """取消任务"""
        for task in self._task_queue:
            if task.get('id') == task_id:
                if task.get('status') == 'running':
                    task['status'] = 'cancelled'
                    task['message'] = '任务已取消'
                    task['updatedAt'] = datetime.now().isoformat()
                    self._save_task_queue()
                    return {"success": True, "message": "任务已取消"}
                else:
                    return {"success": False, "message": "任务不在运行中"}
        return {"success": False, "message": "任务不存在"}
    
    def get_movie(self, movie_id: int):
        """获取单个电影信息"""
        movies = self.get_movies()
        for movie in movies:
            if movie.get('id') == movie_id:
                return movie
        return None
    
    def get_tvshow(self, show_id: int):
        """获取单个电视剧信息"""
        shows = self.get_tvshows()
        for show in shows:
            if show.get('id') == show_id:
                return show
        return None
    
    def get_episodes(self, show_id: int, season_number: int):
        """获取剧集列表"""
        show = self.get_tvshow(show_id)
        if show:
            for season in show.get('seasons', []):
                if season.get('number') == season_number:
                    return season.get('episodes', [])
        return []
    
    def get_anime_show(self, show_id: int):
        """获取单个动漫信息"""
        shows = self.get_anime()
        for show in shows:
            if show.get('id') == show_id:
                return show
        return None
    
    def get_anime_episodes(self, show_id: int, season_number: int):
        """获取动漫剧集列表"""
        show = self.get_anime_show(show_id)
        if show:
            for season in show.get('seasons', []):
                if season.get('number') == season_number:
                    return season.get('episodes', [])
        return []
    
    async def search_movie_subtitles(self, movie_id: int):
        """搜索电影字幕"""
        movie = self.get_movie(movie_id)
        if not movie:
            return []

        # 使用 NFO 解析器获取视频信息（包含 NFO 文件信息）
        video_info = NFOParser.get_video_info_with_nfo(movie['path'])
        return await self._search_subtitles(video_info)
    
    async def upload_subtitle(self, show_id: int, season_number: int, episode_id: str, subtitle_file):
        """上传字幕"""
        return {"success": True}
    
    async def upload_single_subtitle(self, episode_id: str, subtitle_file):
        """上传单个字幕"""
        return {"success": True}
    
    def get_settings(self):
        """获取设置"""
        return {
            'movieDir': settings.MOVIE_DIR,
            'tvDir': settings.TV_DIR,
            'animeDir': settings.ANIME_DIR,
            'scanInterval': settings.SCAN_INTERVAL,
            'minFileSize': settings.MIN_FILE_SIZE_MB,
            'maxConcurrent': settings.MAX_CONCURRENT_DOWNLOADS,
            'subtitleSources': settings.SUBTITLE_SOURCES.split(','),
            'openSubtitlesApiKey': settings.OPENSUBTITLES_API_KEY or '',
            'openSubtitlesUsername': settings.OPENSUBTITLES_USERNAME or '',
            'openSubtitlesPassword': settings.OPENSUBTITLES_PASSWORD or '',
            'tmdbApiKey': settings.TMDB_API_KEY or '',
            'plexNamingFormat': settings.PLEX_NAMING_FORMAT,
            'plexServerUrl': settings.PLEX_SERVER_URL or '',
            'plexToken': settings.PLEX_TOKEN or '',
            'plexRefreshAfterDownload': settings.PLEX_REFRESH_AFTER_DOWNLOAD,
            'plexPathMappings': settings.PLEX_PATH_MAPPINGS or '',
            'autoDownloadDelayMinSeconds': settings.AUTO_DOWNLOAD_DELAY_MIN_SECONDS,
            'autoDownloadDelayMaxSeconds': settings.AUTO_DOWNLOAD_DELAY_MAX_SECONDS,
            'autoDownload': settings.AUTO_DOWNLOAD,
            'backupExisting': settings.BACKUP_EXISTING_SUBTITLE,
            'logLevel': settings.LOG_LEVEL,
            'nastoolEnabled': settings.NASTOOL_ENABLED,
            'nastoolWebhookToken': settings.NASTOOL_WEBHOOK_TOKEN or '',
            'nastoolPathMappings': settings.NASTOOL_PATH_MAPPINGS or ''
        }
    
    def update_settings(self, settings_data: dict):
        """更新设置"""
        try:
            import json
            auto_delay_min = max(0, int(settings_data.get('autoDownloadDelayMinSeconds', 6)))
            auto_delay_max = max(auto_delay_min, int(settings_data.get('autoDownloadDelayMaxSeconds', 14)))
            
            # 读取当前 .env 文件
            env_path = '/app/.env'
            env_lines = []
            
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    env_lines = f.readlines()
            
            # 构建新的配置字典
            new_settings = {
                'MOVIE_DIR': settings_data.get('movieDir', '/movies'),
                'TV_DIR': settings_data.get('tvDir', '/tvshows'),
                'ANIME_DIR': settings_data.get('animeDir', '/anime'),
                'SCAN_INTERVAL': str(settings_data.get('scanInterval', 30)),
                'MIN_FILE_SIZE_MB': str(settings_data.get('minFileSize', 100)),
                'MAX_CONCURRENT_DOWNLOADS': str(settings_data.get('maxConcurrent', 3)),
                'SUBTITLE_SOURCES': ','.join(settings_data.get('subtitleSources', ['shooter', 'assrt', 'opensubtitles', 'subhd'])),
                'OPENSUBTITLES_API_KEY': settings_data.get('openSubtitlesApiKey', ''),
                'OPENSUBTITLES_USERNAME': settings_data.get('openSubtitlesUsername', ''),
                'OPENSUBTITLES_PASSWORD': settings_data.get('openSubtitlesPassword', ''),
                'TMDB_API_KEY': settings_data.get('tmdbApiKey', ''),
                'PLEX_NAMING_FORMAT': 'true' if settings_data.get('plexNamingFormat', True) else 'false',
                'PLEX_SERVER_URL': settings_data.get('plexServerUrl', ''),
                'PLEX_TOKEN': settings_data.get('plexToken', ''),
                'PLEX_REFRESH_AFTER_DOWNLOAD': 'true' if settings_data.get('plexRefreshAfterDownload', True) else 'false',
                'PLEX_PATH_MAPPINGS': settings_data.get('plexPathMappings', ''),
                'AUTO_DOWNLOAD_DELAY_MIN_SECONDS': str(auto_delay_min),
                'AUTO_DOWNLOAD_DELAY_MAX_SECONDS': str(auto_delay_max),
                'AUTO_DOWNLOAD': 'true' if settings_data.get('autoDownload', True) else 'false',
                'BACKUP_EXISTING_SUBTITLE': 'true' if settings_data.get('backupExisting', False) else 'false',
                'LOG_LEVEL': settings_data.get('logLevel', 'INFO'),
                'NASTOOL_ENABLED': 'true' if settings_data.get('nastoolEnabled', False) else 'false',
                'NASTOOL_WEBHOOK_TOKEN': settings_data.get('nastoolWebhookToken', ''),
                'NASTOOL_PATH_MAPPINGS': settings_data.get('nastoolPathMappings', ''),
            }
            
            # 写入 .env 文件
            with open(env_path, 'w', encoding='utf-8') as f:
                for key, value in new_settings.items():
                    f.write(f'{key}={value}\n')
            
            # 同时备份到数据目录（持久化存储）
            try:
                backup_path = '/app/data/.env.backup'
                os.makedirs('/app/data', exist_ok=True)
                with open(backup_path, 'w', encoding='utf-8') as f:
                    for key, value in new_settings.items():
                        f.write(f'{key}={value}\n')
                logger.info(f"配置已备份到: {backup_path}")
            except Exception as e:
                logger.warning(f"备份配置失败: {e}")
            
            # 更新当前 settings 对象
            settings.MOVIE_DIR = new_settings['MOVIE_DIR']
            settings.TV_DIR = new_settings['TV_DIR']
            settings.ANIME_DIR = new_settings['ANIME_DIR']
            settings.SCAN_INTERVAL = int(new_settings['SCAN_INTERVAL'])
            settings.MIN_FILE_SIZE_MB = int(new_settings['MIN_FILE_SIZE_MB'])
            settings.MAX_CONCURRENT_DOWNLOADS = int(new_settings['MAX_CONCURRENT_DOWNLOADS'])
            settings.SUBTITLE_SOURCES = new_settings['SUBTITLE_SOURCES']
            settings.OPENSUBTITLES_API_KEY = new_settings['OPENSUBTITLES_API_KEY'] or None
            settings.OPENSUBTITLES_USERNAME = new_settings['OPENSUBTITLES_USERNAME'] or None
            settings.OPENSUBTITLES_PASSWORD = new_settings['OPENSUBTITLES_PASSWORD'] or None
            settings.TMDB_API_KEY = new_settings['TMDB_API_KEY'] or None
            settings.PLEX_NAMING_FORMAT = new_settings['PLEX_NAMING_FORMAT'] == 'true'
            settings.PLEX_SERVER_URL = new_settings['PLEX_SERVER_URL'] or None
            settings.PLEX_TOKEN = new_settings['PLEX_TOKEN'] or None
            settings.PLEX_REFRESH_AFTER_DOWNLOAD = new_settings['PLEX_REFRESH_AFTER_DOWNLOAD'] == 'true'
            settings.PLEX_PATH_MAPPINGS = new_settings['PLEX_PATH_MAPPINGS'] or None
            settings.AUTO_DOWNLOAD_DELAY_MIN_SECONDS = int(new_settings['AUTO_DOWNLOAD_DELAY_MIN_SECONDS'])
            settings.AUTO_DOWNLOAD_DELAY_MAX_SECONDS = int(new_settings['AUTO_DOWNLOAD_DELAY_MAX_SECONDS'])
            settings.AUTO_DOWNLOAD = new_settings['AUTO_DOWNLOAD'] == 'true'
            settings.BACKUP_EXISTING_SUBTITLE = new_settings['BACKUP_EXISTING_SUBTITLE'] == 'true'
            settings.LOG_LEVEL = new_settings['LOG_LEVEL']
            settings.NASTOOL_ENABLED = new_settings['NASTOOL_ENABLED'] == 'true'
            settings.NASTOOL_WEBHOOK_TOKEN = new_settings['NASTOOL_WEBHOOK_TOKEN'] or None
            settings.NASTOOL_PATH_MAPPINGS = new_settings['NASTOOL_PATH_MAPPINGS'] or None

            # 重新初始化 TMDB API
            tmdb_module.init_tmdb_api(settings.TMDB_API_KEY)
            
            logger.info("设置已更新并保存到 .env 文件")
            
            # 重新加载配置
            from backend.config import reload_settings
            new_settings = reload_settings()
            
            # 使用新配置重新初始化 TMDB API
            tmdb_module.init_tmdb_api(new_settings.TMDB_API_KEY)
            
            return {"success": True, "message": "设置已保存"}
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            return {"success": False, "message": str(e)}
    
    def get_recent_activity(self, limit: int = 10):
        """获取最近活动"""
        return []

    def get_tvshows(self) -> list:
        """Return normalized TV library data."""
        cached = self._get_cached_library("tvshows")
        if cached is not None:
            return cached
        shows = self._scan_series_library(config.TV_DIR, "tv")
        self._set_cached_library("tvshows", shows)
        return shows

    def get_anime(self) -> list:
        """Return normalized anime library data."""
        cached = self._get_cached_library("anime")
        if cached is not None:
            return cached
        shows = self._scan_series_library(config.ANIME_DIR, "anime")
        self._set_cached_library("anime", shows)
        return shows

    async def download_movie_subtitle(self, movie_id: int, subtitle_id: str, source_name: str = None, subtitle_result: dict = None):
        """Download a movie subtitle."""
        movie = self.get_movie(movie_id)
        if not movie:
            return {"success": False, "message": "电影不存在"}

        return await self._download_subtitle_for_video(
            movie['path'],
            subtitle_id,
            source_name,
            subtitle_result
        )

    async def search_episode_subtitles(self, episode_id: str):
        """Search subtitles for a TV episode."""
        episode = self._find_episode_by_id(self.get_tvshows(), episode_id)
        if not episode:
            episode = self._find_episode_by_id(self.get_anime(), episode_id)
        if not episode:
            return []

        video_info = NFOParser.get_video_info_with_nfo(episode['path'])
        return await self._search_subtitles(video_info)

    async def download_episode_subtitle(self, episode_id: str, subtitle_id: str, source_name: str = None, subtitle_result: dict = None):
        """Download a subtitle for a TV episode."""
        episode = self._find_episode_by_id(self.get_tvshows(), episode_id)
        if not episode:
            return {"success": False, "message": "剧集不存在"}

        return await self._download_subtitle_for_video(
            episode['path'],
            subtitle_id,
            source_name,
            subtitle_result
        )

    async def search_anime_subtitles(self, episode_id: str):
        """Search subtitles for an anime episode."""
        episode = self._find_episode_by_id(self.get_anime(), episode_id)
        if not episode:
            return []

        video_info = NFOParser.get_video_info_with_nfo(episode['path'])
        return await self._search_subtitles(video_info)

    async def download_anime_subtitle(self, episode_id: str, subtitle_id: str, source_name: str = None, subtitle_result: dict = None):
        """Download a subtitle for an anime episode."""
        episode = self._find_episode_by_id(self.get_anime(), episode_id)
        if not episode:
            return {"success": False, "message": "动漫不存在"}

        return await self._download_subtitle_for_video(
            episode['path'],
            subtitle_id,
            source_name,
            subtitle_result
        )

    def get_movie_subtitles(self, movie_id: int):
        """List subtitle files for a movie."""
        try:
            movie = self.get_movie(movie_id)
            if not movie:
                return {"success": False, "message": "电影不存在"}

            video_path = movie.get('path')
            if not video_path or not os.path.exists(video_path):
                return {"success": False, "message": "视频文件不存在"}

            subtitles = self._collect_video_subtitles(video_path)
            return {
                "success": True,
                "subtitles": subtitles,
                "count": len(subtitles)
            }
        except Exception as e:
            logger.error(f"获取电影字幕列表失败: {e}")
            return {"success": False, "message": str(e)}

    def get_episode_subtitles(self, episode_id: str):
        """List subtitle files for a TV episode."""
        episode = self._find_episode_by_id(self.get_tvshows(), episode_id)
        if not episode:
            episode = self._find_episode_by_id(self.get_anime(), episode_id)
        if not episode:
            return {"success": False, "message": "剧集不存在"}

        try:
            video_path = episode.get('path')
            if not video_path or not os.path.exists(video_path):
                return {"success": False, "message": "视频文件不存在"}

            subtitles = self._collect_video_subtitles(video_path)
            return {
                "success": True,
                "subtitles": subtitles,
                "count": len(subtitles)
            }
        except Exception as e:
            logger.error(f"获取剧集字幕列表失败: {e}")
            return {"success": False, "message": str(e)}

    def delete_subtitle(self, subtitle_path: str):
        """删除字幕文件"""
        try:
            # 安全检查 1: 检查文件是否存在
            if not os.path.exists(subtitle_path):
                return {"success": False, "message": "字幕文件不存在"}

            # 安全检查 2: 路径穿越防护 - 解析真实路径并验证
            try:
                real_subtitle_path = str(Path(subtitle_path).resolve())
                real_watch_dirs = [str(Path(d).resolve()) for d in settings.get_watch_dirs()]
            except Exception as e:
                logger.error(f"路径解析失败: {subtitle_path}, 错误: {e}")
                return {"success": False, "message": "路径格式无效"}

            # 确保删除的文件在监控目录内
            is_in_watch_dir = any(
                real_subtitle_path.startswith(watched_dir)
                for watched_dir in real_watch_dirs
            )

            if not is_in_watch_dir:
                logger.warning(f"拒绝删除非监控目录文件: {real_subtitle_path}, 监控目录: {real_watch_dirs}")
                return {"success": False, "message": "字幕文件不在监控目录内，无法删除"}

            # 安全检查 3: 防止目录遍历攻击 - 确保文件名不包含路径分隔符
            if '/' in os.path.basename(subtitle_path) or '\\' in os.path.basename(subtitle_path):
                return {"success": False, "message": "文件名包含非法字符"}

            # 删除文件
            os.remove(real_subtitle_path)
            logger.info(f"已删除字幕文件: {real_subtitle_path}")
            self._invalidate_library_cache()

            return {"success": True, "message": "字幕文件已删除"}

        except Exception as e:
            logger.error(f"删除字幕文件失败: {e}")
            return {"success": False, "message": str(e)}

    def _parse_subtitle_language(self, filename: str) -> str:
        """从文件名解析字幕语言"""
        filename_lower = filename.lower()

        # 检查 PLEX 命名格式: .zh.srt, .en.srt, .zh-cn.srt 等
        language_codes = {
            'zh-cn': '简体中文',
            'zh-tw': '繁体中文',
            'zh-hk': '繁体中文',
            'zh': '中文',
            'cn': '中文',
            'en': '英文',
            'ja': '日文',
            'jp': '日文',
            'ko': '韩文',
            'kr': '韩文',
            'fr': '法文',
            'de': '德文',
            'es': '西班牙文',
            'it': '意大利文',
            'ru': '俄文',
            'pt': '葡萄牙文',
        }

        for code, name in language_codes.items():
            if f'.{code}.' in filename_lower or f'.{code}-' in filename_lower:
                return name

        # 检查中文标识
        if 'chinese' in filename_lower or '中文' in filename:
            return '中文'
        if 'english' in filename_lower or '英文' in filename:
            return '英文'

        return '未知'

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    async def search_and_download_subtitle(self, video_info: dict) -> bool:
        """
        搜索并下载字幕（用于 NASTool Webhook 对接）
        
        Args:
            video_info: 视频信息字典
            
        Returns:
            是否成功下载字幕
        """
        try:
            video_path = video_info.get('path')
            if not video_path or not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return False
            
            # 检查是否已有中文字幕
            if has_chinese_subtitle(video_path):
                logger.info(f"视频已有中文字幕，跳过: {video_path}")
                return True
            
            # 搜索字幕
            logger.info(f"开始搜索字幕: {video_info.get('name', video_path)}")
            await self._throttle_auto_requests("搜索字幕", video_info.get('name', video_path))
            results = await self._search_subtitles(video_info)
            
            if not results:
                logger.warning(f"未找到字幕: {video_info.get('name', video_path)}")
                return False
            
            # 选择最佳字幕（第一个结果）
            best_result = results[0]
            logger.info(f"找到最佳字幕: {best_result.title} (来源: {best_result.source}, 评分: {best_result.score})")
            
            # 确定字幕保存路径
            subtitle_path = get_subtitle_save_path(
                video_path,
                lang_code="zh-cn",
                plex_format=settings.PLEX_NAMING_FORMAT
            )
            before_paths = set(self._get_subtitle_candidates(video_path))
            
            # 获取字幕源
            source = get_source(best_result.source)
            if not source:
                logger.error(f"字幕源未找到: {best_result.source}")
                return False
            
            # 下载字幕
            await self._throttle_auto_requests("下载字幕", video_info.get('name', video_path))
            download_state = await source.download(best_result, subtitle_path)
            
            if download_state:
                actual_path = self._resolve_downloaded_subtitle_path(
                    download_result=download_state,
                    video_path=video_path,
                    requested_path=subtitle_path,
                    before_paths=before_paths,
                )
                if not actual_path:
                    logger.error("字幕下载成功但未找到保存文件")
                    return False
                normalized = self._normalize_downloaded_subtitle(video_path, actual_path)
                plex_refresh = await self._refresh_plex_media(video_path)
                self._mark_cached_video_has_subtitle(video_path, True)
                logger.info(f"字幕下载成功: {normalized['path']} (plex={plex_refresh})")
                return True
            else:
                logger.error(f"字幕下载失败: {best_result.title}")
                return False
                
        except Exception as e:
            logger.error(f"搜索并下载字幕失败: {e}")
            return False
