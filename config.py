from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # 监控目录 - nastools 生成的硬链接目录 (逗号分隔的字符串)
    WATCH_DIRS: str = "/movies"
    
    # 扫描间隔（分钟）
    SCAN_INTERVAL: int = 30
    
    # 支持的视频格式
    VIDEO_EXTENSIONS: List[str] = [".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".m4v"]
    
    # 支持的字幕格式
    SUBTITLE_EXTENSIONS: List[str] = [".srt", ".ass", ".ssa", ".vtt", ".sub"]
    
    # 字幕语言标识
    CHINESE_LANG_CODES: List[str] = ["zh", "chi", "chs", "cht", "cn", "zh-cn", "zh-tw", "zh-hk"]
    
    # 字幕下载源
    SUBTITLE_SOURCES: str = "subhd,zimuku,opensubtitles"
    
    # 文件大小阈值（MB），小于此值的文件跳过
    MIN_FILE_SIZE_MB: int = 100
    
    # 日志级别
    LOG_LEVEL: str = "INFO"
    
    # OpenSubtitles API 配置（可选）
    OPENSUBTITLES_API_KEY: Optional[str] = None
    OPENSUBTITLES_USERNAME: Optional[str] = None
    OPENSUBTITLES_PASSWORD: Optional[str] = None
    
    # 是否启用自动下载
    AUTO_DOWNLOAD: bool = True
    
    # 下载前是否备份原字幕
    BACKUP_EXISTING_SUBTITLE: bool = False
    
    # 最大并发下载数
    MAX_CONCURRENT_DOWNLOADS: int = 3
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def get_watch_dirs(self) -> List[str]:
        """获取监控目录列表"""
        return [d.strip() for d in self.WATCH_DIRS.split(',') if d.strip()]
    
    def get_subtitle_sources(self) -> List[str]:
        """获取字幕源列表"""
        return [s.strip() for s in self.SUBTITLE_SOURCES.split(',') if s.strip()]


settings = Settings()


# 兼容旧代码的 Config 类
class Config:
    """兼容旧代码的配置类"""
    
    def __init__(self):
        self.WATCH_DIRS = settings.get_watch_dirs()
        self.SCAN_INTERVAL = settings.SCAN_INTERVAL
        self.VIDEO_EXTENSIONS = settings.VIDEO_EXTENSIONS
        self.SUBTITLE_EXTENSIONS = settings.SUBTITLE_EXTENSIONS
        self.CHINESE_LANG_CODES = settings.CHINESE_LANG_CODES
        self.SUBTITLE_SOURCES = settings.get_subtitle_sources()
        self.MIN_FILE_SIZE = settings.MIN_FILE_SIZE_MB * 1024 * 1024
        self.LOG_LEVEL = settings.LOG_LEVEL
        self.OPENSUBTITLES_API_KEY = settings.OPENSUBTITLES_API_KEY
        self.OPENSUBTITLES_USERNAME = settings.OPENSUBTITLES_USERNAME
        self.OPENSUBTITLES_PASSWORD = settings.OPENSUBTITLES_PASSWORD
        self.AUTO_DOWNLOAD = settings.AUTO_DOWNLOAD
        self.BACKUP_EXISTING_SUBTITLE = settings.BACKUP_EXISTING_SUBTITLE
        self.MAX_CONCURRENT_DOWNLOADS = settings.MAX_CONCURRENT_DOWNLOADS
