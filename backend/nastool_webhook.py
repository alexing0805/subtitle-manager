"""
NASTool Webhook 对接模块
接收 NASTool 的 Webhook 通知并自动处理字幕下载
"""

import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from pathlib import Path
import asyncio
import os
import time

logger = logging.getLogger(__name__)


class NASToolWebhookData(BaseModel):
    """NASTool Webhook 数据模型"""
    event: str  # 事件类型: download.completed, media.scraped, etc.
    title: Optional[str] = None
    year: Optional[int] = None
    type: Optional[str] = None  # movie, tv, anime
    media_type: Optional[str] = None
    category: Optional[str] = None
    file_path: Optional[str] = None  # 视频文件路径
    file_name: Optional[str] = None  # 视频文件名
    path: Optional[str] = None
    filepath: Optional[str] = None
    target_path: Optional[str] = None
    transfer_path: Optional[str] = None
    source_path: Optional[str] = None
    original_path: Optional[str] = None
    tmdb_id: Optional[str] = None
    imdb_id: Optional[str] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    quality: Optional[str] = None
    site: Optional[str] = None
    message: Optional[str] = None
    # 扩展字段
    media_info: Optional[Dict[str, Any]] = None


class NASToolWebhookHandler:
    """NASTool Webhook 处理器"""
    
    def __init__(self, subtitle_manager):
        self.subtitle_manager = subtitle_manager
        self.supported_events = [
            "download.completed",  # 下载完成
            "media.scraped",       # 媒体刮削完成
            "subtitle.missing",    # 字幕缺失（自定义事件）
            "transfer.completed",  # 文件转移完成
        ]
        self._event_aliases = {
            "download.complete": "download.completed",
            "download.completed": "download.completed",
            "media.scrape": "media.scraped",
            "media.scraped": "media.scraped",
            "subtitle.missing": "subtitle.missing",
            "subtitle-missing": "subtitle.missing",
            "subtitle_missing": "subtitle.missing",
            "transfer.complete": "transfer.completed",
            "transfer.completed": "transfer.completed",
        }
        self._active_tasks: dict[str, asyncio.Task] = {}
        self._recent_triggers: dict[str, float] = {}
        self._dedupe_window_seconds = 120.0
    
    async def handle_webhook(self, data: NASToolWebhookData, token: Optional[str] = None) -> Dict[str, Any]:
        """
        处理 NASTool Webhook 请求
        
        Args:
            data: Webhook 数据
            token: 安全令牌（可选）
            
        Returns:
            处理结果
        """
        from backend.config import settings
        
        # 检查 NASTool 对接是否启用
        if not settings.NASTOOL_ENABLED:
            logger.warning("NASTool 对接未启用")
            return {"status": "disabled", "message": "NASTool 对接未启用"}
        
        # 验证安全令牌（如果配置了）
        if settings.NASTOOL_WEBHOOK_TOKEN and token != settings.NASTOOL_WEBHOOK_TOKEN:
            logger.warning("Webhook 安全令牌验证失败")
            return {"status": "error", "message": "安全令牌验证失败"}
        
        normalized_event = self._normalize_event(data.event)
        resolved_file_path = self._extract_file_path(data)

        logger.info(f"收到 NASTool Webhook: event={normalized_event}, file={resolved_file_path}")
        
        # 检查事件类型
        if normalized_event not in self.supported_events:
            logger.warning(f"不支持的事件类型: {data.event}")
            return {"status": "ignored", "message": f"不支持的事件类型: {data.event}"}
        
        # 检查文件路径
        if not resolved_file_path:
            logger.warning("Webhook 数据缺少文件路径")
            return {"status": "error", "message": "缺少文件路径"}
        
        resolved_path = self._apply_path_mappings(resolved_file_path)

        # 验证文件是否存在
        file_path = Path(resolved_path)
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return {"status": "error", "message": f"文件不存在: {file_path}"}
        
        try:
            # 构建视频信息
            video_info = self._build_video_info(data, str(file_path))

            task_key = self._task_key(video_info)
            now = time.monotonic()
            last_triggered = self._recent_triggers.get(task_key)
            if last_triggered is not None and now - last_triggered < self._dedupe_window_seconds:
                logger.info(f"NASTool 重复事件已抑制: {task_key}")
                return {
                    "status": "ignored",
                    "message": "相同媒体在短时间内已触发过字幕任务",
                    "video_info": video_info,
                }

            active_task = self._active_tasks.get(task_key)
            if active_task and not active_task.done():
                logger.info(f"NASTool 任务已存在，跳过重复事件: {task_key}")
                return {
                    "status": "ignored",
                    "message": "相同媒体已有字幕任务在处理中",
                    "video_info": video_info,
                }
            
            # 异步触发字幕搜索和下载
            self._recent_triggers[task_key] = now
            task = asyncio.create_task(self._process_subtitle_download(video_info))
            self._active_tasks[task_key] = task
            task.add_done_callback(lambda _: self._clear_task_state(task_key))
            
            return {
                "status": "success",
                "message": "字幕下载任务已创建",
                "video_info": video_info
            }
            
        except Exception as e:
            logger.error(f"处理 Webhook 失败: {e}")
            return {"status": "error", "message": str(e)}
    
    def _build_video_info(self, data: NASToolWebhookData, resolved_path: Optional[str] = None) -> Dict[str, Any]:
        """
        从 Webhook 数据构建视频信息
        
        Args:
            data: Webhook 数据
            
        Returns:
            视频信息字典
        """
        media_info = data.media_info or {}
        media_path = resolved_path or self._extract_file_path(data)
        filename = self._first_non_empty(
            data.file_name,
            media_info.get("file_name"),
            media_info.get("filename"),
            Path(media_path).name if media_path else None,
        )

        video_info = {
            "path": media_path,
            "name": filename,
            "filename": filename,
            "type": self._resolve_media_type(data, media_path or ""),
            "title": self._first_non_empty(
                data.title,
                media_info.get("title"),
                media_info.get("name"),
                media_info.get("media_name"),
                Path(filename).stem if filename else None,
            ),
            "year": self._coerce_int(
                data.year,
                media_info.get("year"),
                media_info.get("release_year"),
            ),
            "tmdb_id": self._first_non_empty(data.tmdb_id, media_info.get("tmdb_id"), media_info.get("tmdbid")),
            "imdb_id": self._first_non_empty(data.imdb_id, media_info.get("imdb_id"), media_info.get("imdbid")),
            "season": self._coerce_int(data.season, media_info.get("season"), media_info.get("season_number")),
            "episode": self._coerce_int(data.episode, media_info.get("episode"), media_info.get("episode_number")),
            "quality": self._first_non_empty(data.quality, media_info.get("quality"), media_info.get("video_quality")),
        }
        
        # 从文件名解析季集信息（如果是剧集）
        if video_info["type"] == "tv" and (not data.season or not data.episode):
            season, episode = self._parse_episode_info(video_info["filename"])
            if season:
                video_info["season"] = season
            if episode:
                video_info["episode"] = episode
        
        return video_info

    def _normalize_event(self, event: Optional[str]) -> str:
        raw_event = (event or "").strip().lower()
        normalized = raw_event.replace("_", ".").replace("-", ".")
        return self._event_aliases.get(normalized, normalized)

    def _first_non_empty(self, *values: Any) -> Optional[str]:
        for value in values:
            if isinstance(value, str):
                stripped = value.strip()
                if stripped:
                    return stripped
            elif value is not None:
                return str(value)
        return None

    def _coerce_int(self, *values: Any) -> Optional[int]:
        for value in values:
            if value in (None, ""):
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        return None

    def _extract_file_path(self, data: NASToolWebhookData) -> Optional[str]:
        media_info = data.media_info or {}
        candidates = [
            data.file_path,
            data.path,
            data.filepath,
            data.target_path,
            data.transfer_path,
            data.source_path,
            data.original_path,
            media_info.get("file_path"),
            media_info.get("path"),
            media_info.get("filepath"),
            media_info.get("target_path"),
            media_info.get("transfer_path"),
            media_info.get("source_path"),
            media_info.get("original_path"),
            media_info.get("full_path"),
            media_info.get("save_path"),
            media_info.get("destination"),
            media_info.get("dest"),
        ]
        return self._first_non_empty(*candidates)

    def _resolve_media_type(self, data: NASToolWebhookData, file_path: str) -> str:
        media_info = data.media_info or {}
        raw_type = self._first_non_empty(
            data.type,
            data.media_type,
            data.category,
            media_info.get("type"),
            media_info.get("media_type"),
            media_info.get("category"),
        )

        if raw_type:
            normalized = raw_type.strip().lower()
            if normalized in {"tv", "series", "show", "episode", "season", "电视剧"}:
                return "tv"
            if normalized in {"anime", "animation", "动漫", "动画", "动画片"}:
                return "anime"
            if normalized in {"movie", "film", "电影"}:
                return "movie"

        return self._detect_type(file_path)

    def _parse_path_mappings(self) -> list[tuple[str, str]]:
        from backend.config import settings

        raw_value = settings.NASTOOL_PATH_MAPPINGS or ""
        mappings = []
        for line in raw_value.splitlines():
            entry = line.strip()
            if not entry or "=" not in entry:
                continue
            source_prefix, target_prefix = entry.split("=", 1)
            source_prefix = source_prefix.strip().rstrip("/\\")
            target_prefix = target_prefix.strip().rstrip("/\\")
            if source_prefix and target_prefix:
                mappings.append((source_prefix, target_prefix))
        mappings.sort(key=lambda item: len(item[0]), reverse=True)
        return mappings

    def _apply_path_mappings(self, file_path: str) -> str:
        normalized_path = os.path.normpath(file_path)
        for source_prefix, target_prefix in self._parse_path_mappings():
            normalized_source = os.path.normpath(source_prefix)
            if normalized_path == normalized_source or normalized_path.startswith(normalized_source + os.sep):
                suffix = normalized_path[len(normalized_source):].lstrip("\\/")
                mapped = os.path.join(target_prefix, suffix) if suffix else target_prefix
                logger.info(f"NASTool 路径映射: {file_path} -> {mapped}")
                return mapped
        return file_path

    def _task_key(self, video_info: Dict[str, Any]) -> str:
        return str(video_info.get("path") or video_info.get("filename") or "").lower()

    def _clear_task_state(self, task_key: str):
        self._active_tasks.pop(task_key, None)
        cutoff = time.monotonic() - self._dedupe_window_seconds
        expired_keys = [key for key, timestamp in self._recent_triggers.items() if timestamp < cutoff]
        for key in expired_keys:
            self._recent_triggers.pop(key, None)
    
    def _detect_type(self, file_path: str) -> str:
        """
        根据文件路径检测视频类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            类型: movie, tv, anime
        """
        path_lower = file_path.lower()
        
        # 检查路径中是否包含动漫相关关键词
        anime_keywords = ["anime", "动漫", "animation", "动画片"]
        for keyword in anime_keywords:
            if keyword in path_lower:
                return "anime"
        
        # 检查是否包含剧集相关关键词
        tv_keywords = ["tv", "tvshows", "电视剧", "series", "show"]
        for keyword in tv_keywords:
            if keyword in path_lower:
                return "tv"
        
        # 检查文件名是否包含季集信息
        if self._has_episode_info(path_lower):
            return "tv"
        
        return "movie"
    
    def _has_episode_info(self, filename: str) -> bool:
        """检查文件名是否包含季集信息"""
        import re
        patterns = [
            r'[Ss]\d{1,2}[Ee]\d{1,2}',  # S01E01
            r'[Ss]\d{1,2}\s*[Ee]\d{1,2}',  # S01 E01
            r'\d{1,2}[Xx]\d{1,2}',  # 1x01
            r'第\s*\d+\s*集',  # 第01集
            r'[Ee][Pp]?\s*\d+',  # EP01, E01
        ]
        for pattern in patterns:
            if re.search(pattern, filename):
                return True
        return False
    
    def _parse_episode_info(self, filename: str) -> tuple:
        """
        从文件名解析季集信息
        
        Args:
            filename: 文件名
            
        Returns:
            (season, episode) 元组，解析失败返回 (None, None)
        """
        import re
        
        # 尝试匹配 S01E01 格式
        match = re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})', filename)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        # 尝试匹配 1x01 格式
        match = re.search(r'(\d{1,2})[Xx](\d{1,2})', filename)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        # 尝试匹配第几季第几集格式
        match = re.search(r'第\s*(\d+)\s*季.*第\s*(\d+)\s*集', filename)
        if match:
            return int(match.group(1)), int(match.group(2))
        
        return None, None
    
    async def _process_subtitle_download(self, video_info: Dict[str, Any]):
        """
        处理字幕下载
        
        Args:
            video_info: 视频信息
        """
        try:
            logger.info(f"开始为 {video_info['name']} 搜索字幕...")
            
            # 调用字幕管理器搜索和下载字幕
            result = await self.subtitle_manager.search_and_download_subtitle(video_info)
            
            if result:
                logger.info(f"字幕下载成功: {video_info['name']}")
            else:
                logger.warning(f"未找到合适的字幕: {video_info['name']}")
                
        except Exception as e:
            logger.error(f"字幕下载失败: {e}")


# NASTool 事件类型说明
NASTOOL_EVENTS = {
    "download.completed": "下载完成",
    "media.scraped": "媒体刮削完成",
    "media.deleted": "媒体删除",
    "transfer.completed": "文件转移完成",
}
