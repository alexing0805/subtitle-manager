import os
import asyncio
import json
from datetime import datetime
from typing import List, Optional, Set
from pathlib import Path
from loguru import logger
import aiohttp

from config import settings
from utils import (
    get_video_files, has_chinese_subtitle, extract_video_info,
    get_subtitle_save_path, is_movie_file, is_tv_episode
)
from subtitle_sources import get_source, SubtitleResult


class SubtitleManager:
    """字幕管理器"""
    
    def __init__(self):
        self.processed_files: Set[str] = set()
        self.failed_files: dict = {}  # 记录失败次数
        self.history_file = "/app/data/history.json"
        self.load_history()
    
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
    
    async def scan_and_process(self):
        """扫描并处理所有监控目录"""
        logger.info("开始扫描监控目录...")
        
        all_video_files = []
        for watch_dir in settings.WATCH_DIRS:
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
                    success = await source.download(subtitle, save_path)
                    if success:
                        # 验证下载的字幕
                        if has_chinese_subtitle(video_path):
                            logger.info(f"字幕下载并验证成功: {save_path}")
                            self.processed_files.add(file_hash)
                            # 清除失败记录
                            if file_hash in self.failed_files:
                                del self.failed_files[file_hash]
                            return True
                        else:
                            logger.warning(f"下载的字幕验证失败，尝试下一个")
                            # 删除无效字幕文件
                            try:
                                if os.path.exists(save_path):
                                    os.remove(save_path)
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
        """从多个源搜索字幕"""
        all_results = []
        
        # 并发搜索所有字幕源
        tasks = []
        for source_name in settings.SUBTITLE_SOURCES:
            source = get_source(source_name)
            if source:
                task = source.search(video_info)
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    all_results.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"搜索字幕源异常: {result}")
        
        # 过滤非中文字幕
        chinese_results = [
            r for r in all_results 
            if r.language.lower() in ['zh', 'zh-cn', 'zh-tw', 'zh-hk', 'chi', 'chs', 'cht', 'cn']
        ]
        
        logger.info(f"找到 {len(chinese_results)} 个中文字幕")
        return chinese_results
    
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
        return {
            'processed_count': len(self.processed_files),
            'failed_count': len(self.failed_files),
            'failed_files': self.failed_files
        }
