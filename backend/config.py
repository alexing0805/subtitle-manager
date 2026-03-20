"""
配置管理模块 - 支持配置持久化和热重载
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置类"""
    
    # 监控目录 - 电影、电视剧、动漫目录
    MOVIE_DIR: str = "/movies"
    TV_DIR: str = "/tvshows"
    ANIME_DIR: str = "/anime"
    
    # 扫描间隔（分钟）
    SCAN_INTERVAL: int = 30
    
    # 支持的视频格式
    VIDEO_EXTENSIONS: List[str] = [".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".m4v"]
    
    # 支持的字幕格式
    SUBTITLE_EXTENSIONS: List[str] = [".srt", ".ass", ".ssa", ".vtt", ".smi", ".sami", ".sub", ".idx", ".sup"]
    
    # 字幕语言标识
    CHINESE_LANG_CODES: List[str] = ["zh", "chi", "chs", "cht", "cn", "zh-cn", "zh-tw", "zh-hk"]
    
    # 字幕下载源 (按优先级排序)
    SUBTITLE_SOURCES: str = "shooter,assrt,opensubtitles,subhd"
    
    # 文件大小阈值（MB），小于此值的文件跳过
    MIN_FILE_SIZE_MB: int = 100
    
    # 日志级别
    LOG_LEVEL: str = "INFO"
    
    # OpenSubtitles API 配置（可选）
    OPENSUBTITLES_API_KEY: Optional[str] = None
    OPENSUBTITLES_USERNAME: Optional[str] = None
    OPENSUBTITLES_PASSWORD: Optional[str] = None

    # TMDB API 配置（可选，用于获取标准电影信息）
    TMDB_API_KEY: Optional[str] = None

    # 是否启用自动下载
    AUTO_DOWNLOAD: bool = True

    # 自动下载请求节流（秒）
    AUTO_DOWNLOAD_DELAY_MIN_SECONDS: int = 6
    AUTO_DOWNLOAD_DELAY_MAX_SECONDS: int = 14

    # 是否使用 PLEX 字幕命名格式
    PLEX_NAMING_FORMAT: bool = True

    # Plex 集成配置
    PLEX_SERVER_URL: Optional[str] = None
    PLEX_TOKEN: Optional[str] = None
    PLEX_REFRESH_AFTER_DOWNLOAD: bool = True
    PLEX_PATH_MAPPINGS: Optional[str] = None
    
    # 下载前是否备份原字幕
    BACKUP_EXISTING_SUBTITLE: bool = False
    
    # 最大并发下载数
    MAX_CONCURRENT_DOWNLOADS: int = 3
    
    # NASTool Webhook 配置
    NASTOOL_ENABLED: bool = False  # 是否启用 NASTool 对接
    NASTOOL_WEBHOOK_TOKEN: Optional[str] = None  # Webhook 安全令牌（可选）
    NASTOOL_PATH_MAPPINGS: Optional[str] = None  # NASTool 路径映射（NASTool路径=容器路径）
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    def get_watch_dirs(self) -> List[str]:
        """获取监控目录列表"""
        dirs = []
        if self.MOVIE_DIR:
            dirs.append(self.MOVIE_DIR)
        if self.TV_DIR:
            dirs.append(self.TV_DIR)
        if self.ANIME_DIR:
            dirs.append(self.ANIME_DIR)
        return [d.strip() for d in dirs if d.strip()]
    
    def get_subtitle_sources(self) -> List[str]:
        """获取字幕源列表"""
        return [s.strip() for s in self.SUBTITLE_SOURCES.split(',') if s.strip()]


def restore_config_from_backup():
    """从备份恢复配置到 .env 文件"""
    env_path = '.env'
    backup_path = '/app/data/.env.backup'
    
    # 如果 .env 不存在但有备份，从备份恢复
    if not os.path.exists(env_path) and os.path.exists(backup_path):
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[Config] 配置已从备份恢复: {backup_path} -> {env_path}")
            return True
        except Exception as e:
            print(f"[Config] 从备份恢复配置失败: {e}")
    return False


def load_settings() -> Settings:
    """加载设置 - 每次调用都会重新读取配置文件"""
    # 尝试从备份恢复
    restore_config_from_backup()
    
    # 创建新的 Settings 实例（会重新读取 .env 文件）
    return Settings()


# 全局设置实例 - 首次加载
settings = load_settings()


def reload_settings():
    """重新加载设置（热重载）"""
    global settings
    settings = load_settings()
    print("[Config] 配置已重新加载")
    return settings


# 兼容旧代码的 Config 类
class Config:
    """兼容旧代码的配置类"""
    
    def __init__(self):
        self._refresh()
    
    def _refresh(self):
        """从全局 settings 刷新配置"""
        self.MOVIE_DIR = settings.MOVIE_DIR
        self.TV_DIR = settings.TV_DIR
        self.ANIME_DIR = settings.ANIME_DIR
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
        self.TMDB_API_KEY = settings.TMDB_API_KEY
        self.AUTO_DOWNLOAD = settings.AUTO_DOWNLOAD
        self.AUTO_DOWNLOAD_DELAY_MIN_SECONDS = settings.AUTO_DOWNLOAD_DELAY_MIN_SECONDS
        self.AUTO_DOWNLOAD_DELAY_MAX_SECONDS = settings.AUTO_DOWNLOAD_DELAY_MAX_SECONDS
        self.BACKUP_EXISTING_SUBTITLE = settings.BACKUP_EXISTING_SUBTITLE
        self.MAX_CONCURRENT_DOWNLOADS = settings.MAX_CONCURRENT_DOWNLOADS
        self.PLEX_NAMING_FORMAT = settings.PLEX_NAMING_FORMAT
        self.PLEX_SERVER_URL = settings.PLEX_SERVER_URL
        self.PLEX_TOKEN = settings.PLEX_TOKEN
        self.PLEX_REFRESH_AFTER_DOWNLOAD = settings.PLEX_REFRESH_AFTER_DOWNLOAD
        self.PLEX_PATH_MAPPINGS = settings.PLEX_PATH_MAPPINGS
        self.NASTOOL_ENABLED = settings.NASTOOL_ENABLED
        self.NASTOOL_WEBHOOK_TOKEN = settings.NASTOOL_WEBHOOK_TOKEN
        self.NASTOOL_PATH_MAPPINGS = settings.NASTOOL_PATH_MAPPINGS
    
    def get_watch_dirs(self) -> List[str]:
        """获取监控目录列表"""
        self._refresh()  # 每次访问时刷新
        return self.WATCH_DIRS
