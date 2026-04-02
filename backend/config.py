"""
配置管理模块 - 支持配置持久化和热重载
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import json
import os
import tempfile


SETTINGS_JSON_PATH = "/app/data/settings.json"


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
    
    API_KEY: Optional[str] = None

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

    # 字幕格式优先级配置（格式名称=加分值，格式之间逗号分隔）
    # 例如: "srt=0.08,ass=0.06,vtt=0.03,sup=-0.16"
    SUBTITLE_FORMAT_BONUS: str = "srt=0.08,ass=0.06,ssa=0.06,vtt=0.03,smi=0.03,sami=0.03,sup=-0.16,idx=-0.16,sub=-0.16"

    # 库缓存 TTL（秒），文件未变化时使用缓存
    LIBRARY_CACHE_TTL: int = 600  # 默认 10 分钟

    # CORS 来源白名单（逗号分隔），留空则只允许 localhost
    CORS_ORIGINS: str = ""
    
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


def _load_persisted_settings() -> dict:
    """加载用户持久化设置（settings.json）。"""
    if not os.path.exists(SETTINGS_JSON_PATH):
        return {}
    try:
        with open(SETTINGS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"[Config] 加载持久化设置失败: {e}")
        return {}


def save_persisted_settings(settings_data: dict) -> bool:
    """原子保存用户持久化设置（settings.json）。"""
    try:
        os.makedirs(os.path.dirname(SETTINGS_JSON_PATH), exist_ok=True)
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=os.path.dirname(SETTINGS_JSON_PATH), delete=False) as tmp:
            json.dump(settings_data, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = tmp.name
        os.replace(tmp_path, SETTINGS_JSON_PATH)
        return True
    except Exception as e:
        print(f"[Config] 保存持久化设置失败: {e}")
        return False


def _apply_runtime_env(settings_obj: Settings):
    """为仍直接读取 os.environ 的旧模块同步运行时环境变量。"""
    env_map = {
        'API_KEY': settings_obj.API_KEY,
        'OPENSUBTITLES_API_KEY': settings_obj.OPENSUBTITLES_API_KEY,
        'OPENSUBTITLES_USERNAME': settings_obj.OPENSUBTITLES_USERNAME,
        'OPENSUBTITLES_PASSWORD': settings_obj.OPENSUBTITLES_PASSWORD,
        'TMDB_API_KEY': settings_obj.TMDB_API_KEY,
        'PLEX_SERVER_URL': settings_obj.PLEX_SERVER_URL,
        'PLEX_TOKEN': settings_obj.PLEX_TOKEN,
        'PLEX_PATH_MAPPINGS': settings_obj.PLEX_PATH_MAPPINGS,
        'NASTOOL_WEBHOOK_TOKEN': settings_obj.NASTOOL_WEBHOOK_TOKEN,
        'NASTOOL_PATH_MAPPINGS': settings_obj.NASTOOL_PATH_MAPPINGS,
        'SUBTITLE_SOURCES': settings_obj.SUBTITLE_SOURCES,
        'LOG_LEVEL': settings_obj.LOG_LEVEL,
    }
    for key, value in env_map.items():
        if value is None or value == '':
            os.environ.pop(key, None)
        else:
            os.environ[key] = str(value)


def load_settings() -> Settings:
    """加载设置：先读环境/默认值，再应用 settings.json 持久化配置。"""
    loaded = Settings()
    persisted = _load_persisted_settings()
    for key, value in persisted.items():
        if hasattr(loaded, key):
            setattr(loaded, key, value)
    _apply_runtime_env(loaded)
    return loaded


# 全局设置实例 - 首次加载
settings = load_settings()


def reload_settings():
    """重新加载设置（热重载，保留已有对象引用）。"""
    fresh = load_settings()
    for field_name in fresh.model_fields.keys():
        setattr(settings, field_name, getattr(fresh, field_name))
    print("[Config] 配置已重新加载")
    return settings


# 移除 Config 静态兼容类，统一使用全局 settings 对象
