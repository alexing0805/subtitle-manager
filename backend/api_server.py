"""
字幕管理器 API 服务器
提供 RESTful API 供前端调用
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import os
import shutil
import logging
from pathlib import Path
import asyncio
import time
from collections import defaultdict

from backend.subtitle_manager import SubtitleManager
from backend.config import Config, reload_settings, settings
import backend.tmdb_api as tmdb_module
from backend.nastool_webhook import NASToolWebhookHandler, NASToolWebhookData

# 配置日志 - 脱敏敏感信息
class SensitiveFilter(logging.Filter):
    """过滤日志中的敏感信息"""
    SENSITIVE_KEYS = ['token', 'password', 'apikey', 'secret', 'plex_token', 'nastool_webhook_token']
    
    def filter(self, record):
        msg = record.getMessage()
        for key in self.SENSITIVE_KEYS:
            if key in msg.lower():
                # 将敏感值替换为 ***
                import re
                msg = re.sub(rf'({key}[=:]\s*)[^&\s]+', rf'\1***', msg, flags=re.IGNORECASE)
        record.msg = msg
        return True

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.addFilter(SensitiveFilter())

# ==================== API 限流器 ====================

class RateLimiter:
    """
    简单滑动窗口限流器
    默认限制：每分钟 60 次请求
    """
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60.0  # 1分钟窗口
        self._requests: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求，返回 True 表示允许"""
        async with self._lock:
            now = time.monotonic()
            # 清理过期请求
            self._requests[client_id] = [
                t for t in self._requests[client_id]
                if now - t < self.window_size
            ]
            
            if len(self._requests[client_id]) >= self.requests_per_minute:
                return False
            
            self._requests[client_id].append(now)
            return True

rate_limiter = RateLimiter(requests_per_minute=60)


async def rate_limit_middleware(request: Request, call_next):
    """限流中间件 - 忽略健康检查和文档路径"""
    path = request.url.path
    if path in ["/health", "/docs", "/openapi.json", "/redoc"] or path.startswith("/api/poster"):
        return await call_next(request)
    
    client_ip = request.client.host if request.client else "unknown"
    if not await rate_limiter.is_allowed(client_ip):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"detail": "请求过于频繁，请稍后再试"}
        )
    return await call_next(request)


# ==================== CORS 白名单配置 ====================

def get_cors_origins() -> List[str]:
    """
    获取允许的 CORS 来源列表
    从环境变量 CORS_ORIGINS 读取，逗号分隔
    如果未配置，默认只允许同源 + localhost 开发调试
    """
    env_origins = os.environ.get("CORS_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    # 默认允许的开发环境来源
    return [
        "http://localhost:18080",
        "http://localhost:8080",
        "http://127.0.0.1:18080",
        "http://127.0.0.1:8080",
    ]


# 创建 FastAPI 应用
app = FastAPI(
    title="字幕管理器 API",
    description="字幕管理器 RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置 CORS - 从环境变量读取白名单
cors_origins = get_cors_origins()
logger.info(f"CORS 配置: 允许来源 = {cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 注册限流中间件
app.middleware("http")(rate_limit_middleware)

# ==================== API Key 认证 ====================
from fastapi import Header, HTTPException

# ==================== 全局配置和字幕管理器实例
config = Config()
subtitle_manager = SubtitleManager()

# NASTool Webhook 处理器
nastool_webhook_handler = NASToolWebhookHandler(subtitle_manager)


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 重新加载配置（从备份恢复）
    new_settings = reload_settings()
    # 使用新配置重新初始化 TMDB API
    tmdb_module.init_tmdb_api(new_settings.TMDB_API_KEY)
    logger.info("应用启动完成，配置已加载")


# ==================== 健康检查 ====================

class HealthStatus(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    components: Dict[str, str]


@app.get("/health", response_model=HealthStatus, tags=["系统"])
async def health_check():
    """
    健康检查端点
    用于 Docker 健康检查和负载均衡器探测
    """
    from datetime import datetime
    import sys
    import time

    # 基础状态
    components = {
        "api": "healthy",
        "subtitle_manager": "healthy",
        "config": "healthy",
    }

    # 检查字幕管理器
    try:
        stats = subtitle_manager.get_stats()
        if stats:
            components["subtitle_manager"] = "healthy"
    except Exception as e:
        components["subtitle_manager"] = f"unhealthy: {e}"

    # 检查配置文件
    try:
        watch_dirs = settings.get_watch_dirs()
        if not watch_dirs:
            components["config"] = "warning: no watch directories configured"
    except Exception as e:
        components["config"] = f"warning: {e}"

    # 整体状态
    overall_status = "healthy"
    if "unhealthy" in components.get("subtitle_manager", ""):
        overall_status = "unhealthy"

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version="1.0.0",
        uptime_seconds=time.monotonic(),
        components=components
    )


# ==================== 静态文件服务（必须在API路由之前）====================

# 挂载前端静态文件（如果存在）
frontend_path = Path(__file__).resolve().parents[1] / "web" / "dist"
if frontend_path.exists():
    # 挂载静态资源文件
    app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")


# ==================== 数据模型 ====================

class Movie(BaseModel):
    id: int
    name: str
    filename: str
    path: str
    hasSubtitle: bool
    year: Optional[int] = None
    resolution: Optional[str] = None
    size: Optional[int] = None
    posterPath: Optional[str] = None
    fanartPath: Optional[str] = None
    tmdbId: Optional[str] = None
    imdbId: Optional[str] = None
    originalTitle: Optional[str] = None
    nfoPath: Optional[str] = None


class TVShow(BaseModel):
    id: int
    name: str
    year: Optional[int] = None
    posterPath: Optional[str] = None
    fanartPath: Optional[str] = None
    seasonCount: int
    episodeCount: int
    subtitleStats: Dict[str, int]
    seasons: List[Dict[str, Any]]


class SubtitleResult(BaseModel):
    id: str
    title: str
    source: str
    language: str
    score: float
    downloadUrl: Optional[str] = None
    filename: Optional[str] = None  # SubHD 等源的字幕文件名
    summary: Optional[str] = None
    releaseType: Optional[str] = None
    metaTags: List[str] = Field(default_factory=list)
    subtitleFormat: Optional[str] = None

    @field_validator('downloadUrl', mode='before')
    @classmethod
    def validate_downloadUrl(cls, v):
        """确保 downloadUrl 是字符串"""
        if v is None:
            return None
        return str(v)


class Settings(BaseModel):
    movieDir: str
    tvDir: str
    animeDir: str
    scanInterval: int
    minFileSize: int
    maxConcurrent: int
    subtitleSources: List[str]
    openSubtitlesApiKey: Optional[str] = None
    openSubtitlesUsername: Optional[str] = None
    openSubtitlesPassword: Optional[str] = None
    tmdbApiKey: Optional[str] = None
    plexNamingFormat: bool = True
    plexServerUrl: Optional[str] = None
    plexToken: Optional[str] = None
    plexRefreshAfterDownload: bool = True
    plexPathMappings: Optional[str] = None
    autoDownloadDelayMinSeconds: int = 6
    autoDownloadDelayMaxSeconds: int = 14
    autoDownload: bool
    backupExisting: bool
    logLevel: str
    nastoolEnabled: bool = False
    nastoolWebhookToken: Optional[str] = None
    nastoolPathMappings: Optional[str] = None
    apiKey: Optional[str] = None

    @property
    def watchDirs(self) -> str:
        """兼容旧代码：返回逗号分隔的目录字符串"""
        dirs = []
        if self.movieDir:
            dirs.append(self.movieDir)
        if self.tvDir:
            dirs.append(self.tvDir)
        if self.animeDir:
            dirs.append(self.animeDir)
        return ', '.join(dirs)


class Stats(BaseModel):
    totalMovies: int
    moviesWithSubtitle: int
    moviesWithoutSubtitle: int
    totalTVShows: int
    totalEpisodes: int
    episodesWithSubtitle: int
    episodesWithoutSubtitle: int
    totalAnime: int
    animeWithSubtitle: int
    animeWithoutSubtitle: int
    recentDownloads: int
    pendingTasks: int


class BatchUploadRequest(BaseModel):
    showId: int
    seasonNumber: int
    matches: List[Dict[str, Any]]


class DownloadSubtitleRequest(BaseModel):
    subtitle_id: str
    source_name: Optional[str] = None
    subtitle_result: Optional[dict] = None  # 完整的字幕信息（用于 SubHD 等需要直接下载的源）


def serialize_subtitle_result(result: Any) -> SubtitleResult:
    """Convert an internal subtitle result object into the API model."""
    return SubtitleResult(
        id=str(result.id),
        title=result.title,
        source=result.source,
        language=result.language,
        score=result.score,
        downloadUrl=result.download_url,
        filename=getattr(result, 'filename', None),
        summary=getattr(result, 'summary', None),
        releaseType=getattr(result, 'release_type', None),
        metaTags=list(getattr(result, 'meta_tags', []) or []),
        subtitleFormat=getattr(result, 'file_format', None),
    )


# ==================== API 路由 ====================

# 根路径 - 返回前端页面
@app.get("/", response_class=FileResponse)
async def serve_index():
    """服务首页"""
    if frontend_path.exists():
        return FileResponse(str(frontend_path / "index.html"))
    return {
        "message": "字幕管理器 API",
        "version": "1.0.0",
        "status": "running"
    }


# -------------------- 统计信息 --------------------

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """获取统计信息"""
    try:
        stats = subtitle_manager.get_stats()
        return Stats(**stats)
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recent-activity")
async def get_recent_activity(limit: int = 10):
    """获取最近活动"""
    try:
        activities = subtitle_manager.get_recent_activity(limit)
        return activities
    except Exception as e:
        logger.error(f"获取最近活动失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 电影管理 --------------------

@app.get("/api/movies", response_model=List[Movie])
async def get_movies():
    """获取电影列表"""
    try:
        movies = subtitle_manager.get_movies()
        return [Movie(**movie) for movie in movies]
    except Exception as e:
        logger.error(f"获取电影列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/movies/{movie_id}", response_model=Movie)
async def get_movie(movie_id: int):
    """获取单个电影信息"""
    try:
        movie = subtitle_manager.get_movie(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="电影不存在")
        return Movie(**movie)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取电影信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/movies/{movie_id}/search-subtitles")
async def search_movie_subtitles(movie_id: int):
    """搜索电影字幕"""
    try:
        results = await subtitle_manager.search_movie_subtitles(movie_id)
        return [serialize_subtitle_result(result) for result in results]
    except Exception as e:
        logger.error(f"搜索字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/movies/{movie_id}/download-subtitle")
async def download_movie_subtitle(movie_id: int, request: DownloadSubtitleRequest):
    """下载电影字幕"""
    try:
        logger.info(f"下载字幕请求: movie_id={movie_id}, subtitle_id={request.subtitle_id}, source_name={request.source_name}")
        logger.info(f"subtitle_result: {request.subtitle_result}")
        result = await subtitle_manager.download_movie_subtitle(
            movie_id, request.subtitle_id, request.source_name, 
            subtitle_result=request.subtitle_result
        )
        if result.get("success"):
            return {"success": True, "message": "字幕下载成功", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "下载失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 电视剧管理 --------------------

@app.get("/api/tvshows", response_model=List[TVShow])
async def get_tvshows():
    """获取电视剧列表"""
    try:
        shows = subtitle_manager.get_tvshows()
        return [TVShow(**show) for show in shows]
    except Exception as e:
        logger.error(f"获取电视剧列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tvshows/{show_id}", response_model=TVShow)
async def get_tvshow(show_id: int):
    """获取单个电视剧信息"""
    try:
        show = subtitle_manager.get_tvshow(show_id)
        if not show:
            raise HTTPException(status_code=404, detail="电视剧不存在")
        return TVShow(**show)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取电视剧信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tvshows/{show_id}/seasons/{season_number}/episodes")
async def get_episodes(show_id: int, season_number: int):
    """获取剧集列表"""
    try:
        episodes = subtitle_manager.get_episodes(show_id, season_number)
        return episodes
    except Exception as e:
        logger.error(f"获取剧集列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/episodes/{episode_id}/search-subtitles")
async def search_episode_subtitles(episode_id: str):
    """搜索剧集字幕"""
    try:
        logger.info(f"收到搜索请求: episode_id={episode_id}")
        results = await subtitle_manager.search_episode_subtitles(episode_id)
        logger.info(f"搜索完成，找到 {len(results)} 个字幕")
        
        # 转换为 Pydantic 模型列表
        response_data = []
        for result in results:
            try:
                response_data.append(serialize_subtitle_result(result))
            except Exception as e:
                logger.error(f"转换字幕结果失败: {e}, result={result}")
        
        logger.info(f"返回 {len(response_data)} 个字幕结果")
        for i, item in enumerate(response_data):
            logger.info(f"字幕 {i}: id={item.id}, source={item.source}, filename={item.filename}, title={item.title}")
        return response_data
    except Exception as e:
        logger.error(f"搜索字幕失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/episodes/{episode_id}/download-subtitle")
async def download_episode_subtitle(episode_id: str, request: DownloadSubtitleRequest):
    """下载剧集字幕"""
    try:
        result = await subtitle_manager.download_episode_subtitle(
            episode_id, request.subtitle_id, request.source_name,
            subtitle_result=request.subtitle_result
        )
        if result.get("success"):
            return {"success": True, "message": "字幕下载成功", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "下载失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 动漫管理 --------------------

@app.get("/api/anime", response_model=List[TVShow])
async def get_anime():
    """获取动漫列表"""
    try:
        shows = subtitle_manager.get_anime()
        return [TVShow(**show) for show in shows]
    except Exception as e:
        logger.error(f"获取动漫列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anime/{show_id}", response_model=TVShow)
async def get_anime_show(show_id: int):
    """获取单个动漫信息"""
    try:
        show = subtitle_manager.get_anime_show(show_id)
        if not show:
            raise HTTPException(status_code=404, detail="动漫不存在")
        return TVShow(**show)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取动漫信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/anime/{show_id}/seasons/{season_number}/episodes")
async def get_anime_episodes(show_id: int, season_number: int):
    """获取动漫剧集列表"""
    try:
        episodes = subtitle_manager.get_anime_episodes(show_id, season_number)
        return episodes
    except Exception as e:
        logger.error(f"获取动漫剧集列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/anime/{episode_id}/search-subtitles")
async def search_anime_subtitles(episode_id: str):
    """搜索动漫字幕"""
    try:
        logger.info(f"收到动漫搜索请求: episode_id={episode_id}")
        results = await subtitle_manager.search_anime_subtitles(episode_id)
        logger.info(f"动漫搜索完成，找到 {len(results)} 个字幕")
        
        response_data = []
        for result in results:
            try:
                response_data.append(serialize_subtitle_result(result))
            except Exception as e:
                logger.error(f"转换动漫字幕结果失败: {e}, result={result}")
        
        logger.info(f"返回 {len(response_data)} 个动漫字幕结果")
        return response_data
    except Exception as e:
        logger.error(f"搜索动漫字幕失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/anime/{episode_id}/download-subtitle")
async def download_anime_subtitle(episode_id: str, request: DownloadSubtitleRequest):
    """下载动漫字幕"""
    try:
        result = await subtitle_manager.download_anime_subtitle(
            episode_id, request.subtitle_id, request.source_name,
            subtitle_result=request.subtitle_result
        )
        if result.get("success"):
            return {"success": True, "message": "字幕下载成功", "data": result}
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "下载失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载动漫字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 批量上传字幕 --------------------

@app.post("/api/batch-upload-subtitles")
async def batch_upload_subtitles(
    showId: int = Form(...),
    seasonNumber: int = Form(...),
    files: List[UploadFile] = File(...),
    matches: str = Form(...),  # JSON 字符串
    mediaType: str = Form("tv"),
):
    """批量上传字幕文件"""
    try:
        import json
        matches_data = json.loads(matches)

        results = []
        errors = []
        for match in matches_data:
            file_index = match.get('fileIndex')
            episode_id = match.get('episodeId')

            if file_index is None or file_index >= len(files):
                errors.append({"match": match, "message": "文件索引无效"})
                continue

            result = await subtitle_manager.upload_subtitle(
                show_id=showId,
                season_number=seasonNumber,
                episode_id=episode_id,
                subtitle_file=files[file_index],
                media_type=mediaType,
            )
            if result.get("success"):
                results.append(result)
            else:
                errors.append({"match": match, "message": result.get("message", "上传失败")})

        return {
            "success": len(results) > 0 and not errors,
            "message": f"成功上传 {len(results)} 个字幕" + (f"，失败 {len(errors)} 个" if errors else ""),
            "data": results,
            "errors": errors,
        }
    except Exception as e:
        logger.error(f"批量上传字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 字幕管理 --------------------

@app.get("/api/movies/{movie_id}/subtitles")
async def get_movie_subtitles(movie_id: int):
    """获取电影的所有字幕文件"""
    try:
        result = subtitle_manager.get_movie_subtitles(movie_id)
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "获取失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取电影字幕列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/episodes/{episode_id}/subtitles")
async def get_episode_subtitles(episode_id: str):
    """获取剧集的所有字幕文件"""
    try:
        result = subtitle_manager.get_episode_subtitles(episode_id)
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "获取失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取剧集字幕列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DeleteSubtitleRequest(BaseModel):
    subtitlePath: str


@app.post("/api/subtitles/delete")
async def delete_subtitle(request: DeleteSubtitleRequest):
    """删除字幕文件"""
    try:
        result = subtitle_manager.delete_subtitle(request.subtitlePath)
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "删除失败"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-subtitle")
async def upload_single_subtitle(
    episodeId: str = Form(...),
    file: UploadFile = File(...)
):
    """上传单个字幕文件"""
    try:
        result = await subtitle_manager.upload_single_subtitle(episodeId, file)
        return {"success": True, "message": "字幕上传成功", "data": result}
    except Exception as e:
        logger.error(f"上传字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 设置管理 --------------------

@app.get("/api/settings", response_model=Settings)
async def get_settings():
    """获取设置"""
    try:
        settings = subtitle_manager.get_settings()
        return Settings(**settings)
    except Exception as e:
        logger.error(f"获取设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def update_settings(settings: Settings):
    """更新设置"""
    try:
        result = subtitle_manager.update_settings(settings.dict())
        return {"success": True, "message": "设置已保存", "data": result}
    except Exception as e:
        logger.error(f"更新设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 扫描任务 --------------------

@app.post("/api/scan")
async def trigger_scan(background_tasks: BackgroundTasks):
    """触发扫描任务"""
    try:
        background_tasks.add_task(subtitle_manager.scan_library)
        return {"success": True, "message": "扫描任务已启动"}
    except Exception as e:
        logger.error(f"启动扫描任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """获取服务状态"""
    return {"status": "running", "message": "服务运行正常"}


@app.get("/api/scan/status")
async def get_scan_status():
    """获取扫描状态"""
    try:
        status = subtitle_manager.get_scan_status()
        return status
    except Exception as e:
        logger.error(f"获取扫描状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 任务队列 --------------------

@app.get("/api/tasks")
async def get_tasks():
    """获取任务队列"""
    try:
        tasks = subtitle_manager.get_tasks()
        return tasks
    except Exception as e:
        logger.error(f"获取任务队列失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        result = subtitle_manager.cancel_task(task_id)
        return {"success": True, "message": "任务已取消", "data": result}
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 健康检查 --------------------

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "subtitle-manager"}


# -------------------- 海报图片服务 --------------------

def _pick_existing_image(*paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


def _resolve_media_art(media: Dict[str, Any], preferred: str = "poster") -> Optional[str]:
    poster_path = media.get('posterPath')
    fanart_path = media.get('fanartPath')

    if preferred == "fanart":
        return _pick_existing_image(fanart_path, poster_path)

    return _pick_existing_image(poster_path, fanart_path)


@app.get("/api/poster/{movie_id}")
async def get_poster(movie_id: int):
    """获取电影海报图片"""
    movie = subtitle_manager.get_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="电影不存在")

    poster_path = movie.get('posterPath')
    if not poster_path or not os.path.exists(poster_path):
        raise HTTPException(status_code=404, detail="海报不存在")

    return FileResponse(poster_path)


@app.get("/api/art/movie/{movie_id}")
async def get_movie_art(movie_id: int, preferred: str = "poster"):
    """按偏好获取电影图片，支持 poster/fanart 自动回退"""
    movie = subtitle_manager.get_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="电影不存在")

    art_path = _resolve_media_art(movie, preferred)
    if not art_path:
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(art_path)


@app.get("/api/poster/tvshow/{show_id}")
async def get_tvshow_poster(show_id: int):
    """获取电视剧海报图片"""
    show = subtitle_manager.get_tvshow(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="电视剧不存在")

    poster_path = show.get('posterPath')
    if not poster_path or not os.path.exists(poster_path):
        raise HTTPException(status_code=404, detail="海报不存在")

    return FileResponse(poster_path)


@app.get("/api/art/tvshow/{show_id}")
async def get_tvshow_art(show_id: int, preferred: str = "poster"):
    """按偏好获取电视剧图片，支持 poster/fanart 自动回退"""
    show = subtitle_manager.get_tvshow(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="电视剧不存在")

    art_path = _resolve_media_art(show, preferred)
    if not art_path:
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(art_path)


@app.get("/api/poster/tvshow/{show_id}/season/{season_number}")
async def get_season_poster(show_id: int, season_number: int):
    """获取季海报图片"""
    show = subtitle_manager.get_tvshow(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="电视剧不存在")

    season = None
    for s in show.get('seasons', []):
        if s.get('number') == season_number:
            season = s
            break

    if not season:
        raise HTTPException(status_code=404, detail="季不存在")

    poster_path = season.get('posterPath') or show.get('posterPath')
    if not poster_path or not os.path.exists(poster_path):
        raise HTTPException(status_code=404, detail="海报不存在")

    return FileResponse(poster_path)


# -------------------- TMDB API 测试 --------------------

@app.get("/api/poster/anime/{show_id}")
async def get_anime_poster(show_id: int):
    """获取动漫海报图片"""
    show = subtitle_manager.get_anime_show(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="动漫不存在")

    poster_path = show.get('posterPath')
    if not poster_path or not os.path.exists(poster_path):
        raise HTTPException(status_code=404, detail="海报不存在")

    return FileResponse(poster_path)


@app.get("/api/art/anime/{show_id}")
async def get_anime_art(show_id: int, preferred: str = "poster"):
    """按偏好获取动漫图片，支持 poster/fanart 自动回退"""
    show = subtitle_manager.get_anime_show(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="动漫不存在")

    art_path = _resolve_media_art(show, preferred)
    if not art_path:
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(art_path)


@app.get("/api/poster/anime/{show_id}/season/{season_number}")
async def get_anime_season_poster(show_id: int, season_number: int):
    """获取动漫季度海报URL"""
    show = subtitle_manager.get_anime_show(show_id)
    if not show:
        raise HTTPException(status_code=404, detail="动漫不存在")

    season = None
    for s in show.get('seasons', []):
        if s.get('number') == season_number:
            season = s
            break

    if not season:
        raise HTTPException(status_code=404, detail="季度不存在")

    poster_path = season.get('posterPath') or show.get('posterPath')
    if not poster_path or not os.path.exists(poster_path):
        raise HTTPException(status_code=404, detail="海报不存在")

    return FileResponse(poster_path)


class TMDBTestRequest(BaseModel):
    api_key: str

class TMDBTestResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

@app.post("/api/test-tmdb", response_model=TMDBTestResponse)
async def test_tmdb_api(request: TMDBTestRequest):
    """测试 TMDB API 密钥是否有效"""
    try:
        # 临时初始化 TMDB API
        temp_api = tmdb_module.init_tmdb_api(request.api_key)

        # 测试搜索一个已知电影
        test_result = await temp_api.search_movie("The Matrix", 1999)

        if test_result:
            return {
                "success": True,
                "message": "TMDB API 密钥有效",
                "data": {
                    "test_movie": test_result.get('title'),
                    "year": test_result.get('year'),
                    "imdb_id": test_result.get('imdb_id')
                }
            }
        else:
            return {
                "success": False,
                "message": "API 请求成功但未找到测试电影，请检查密钥权限"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"TMDB API 测试失败: {str(e)}"
        }


# -------------------- NASTool Webhook 对接 --------------------

@app.post("/api/webhook/nastool")
async def nastool_webhook(data: NASToolWebhookData, token: Optional[str] = None):
    """
    接收 NASTool 的 Webhook 通知
    
    配置 NASTool:
    1. 在 NASTool 的"设置" -> "Webhook"中添加 Webhook
    2. URL: http://your-server:18080/api/webhook/nastool?token=your_token（如果设置了安全令牌）
    3. 触发事件: 下载完成、媒体刮削完成
    
    请求体示例:
    {
        "event": "download.completed",
        "title": "电影名称",
        "year": 2023,
        "type": "movie",
        "file_path": "/movies/电影名称 (2023)/电影名称 (2023) - 1080p.mkv",
        "file_name": "电影名称 (2023) - 1080p.mkv",
        "tmdb_id": "12345",
        "imdb_id": "tt1234567",
        "quality": "1080p"
    }
    """
    try:
        result = await nastool_webhook_handler.handle_webhook(data, token)
        return result
    except Exception as e:
        logger.error(f"处理 NASTool Webhook 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/webhook/nastool/test")
async def nastool_webhook_test():
    """测试 NASTool Webhook 接口是否正常工作"""
    return {
        "status": "ok",
        "message": "NASTool Webhook 接口正常运行",
        "supported_events": [
            "download.completed",
            "media.scraped",
            "subtitle.missing",
            "transfer.completed"
        ],
        "endpoint": "/api/webhook/nastool",
        "method": "POST"
    }


# -------------------- 前端路由捕获（必须在最后）--------------------

@app.get("/{path:path}")
async def serve_frontend(path: str):
    """服务前端页面 - 捕获所有非API路径"""
    # API 路径不走前端路由
    if path.startswith("api/") or path in ["health", "docs", "openapi.json", "redoc"]:
        raise HTTPException(status_code=404, detail="Not Found")
    
    # 检查是否是静态资源请求
    if path.startswith("assets/"):
        file_path = frontend_path / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # 如果前端文件存在，返回 index.html
    if frontend_path.exists():
        return FileResponse(str(frontend_path / "index.html"))
    
    # 否则返回 API 信息
    return {
        "message": "字幕管理器 API",
        "version": "1.0.0",
        "status": "running"
    }


# ==================== 启动函数 ====================

def start_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """启动 API 服务器"""
    import uvicorn
    uvicorn.run(
        "backend.api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
