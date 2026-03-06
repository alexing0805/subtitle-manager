"""
字幕管理器 API 服务器
提供 RESTful API 供前端调用
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import shutil
import logging
from pathlib import Path

from subtitle_manager import SubtitleManager
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="字幕管理器 API",
    description="字幕管理器 RESTful API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置和字幕管理器实例
config = Config()
subtitle_manager = SubtitleManager()


# ==================== 静态文件服务（必须在API路由之前）====================

# 挂载前端静态文件（如果存在）
frontend_path = Path(__file__).parent / "web" / "dist"
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


class TVShow(BaseModel):
    id: int
    name: str
    year: Optional[int] = None
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


class Settings(BaseModel):
    watchDirs: str
    scanInterval: int
    minFileSize: int
    maxConcurrent: int
    subtitleSources: List[str]
    openSubtitlesApiKey: Optional[str] = None
    openSubtitlesUsername: Optional[str] = None
    openSubtitlesPassword: Optional[str] = None
    autoDownload: bool
    backupExisting: bool
    logLevel: str


class Stats(BaseModel):
    totalMovies: int
    moviesWithSubtitle: int
    moviesWithoutSubtitle: int
    totalTVShows: int
    totalEpisodes: int
    episodesWithSubtitle: int
    episodesWithoutSubtitle: int
    recentDownloads: int
    pendingTasks: int


class BatchUploadRequest(BaseModel):
    showId: int
    seasonNumber: int
    matches: List[Dict[str, Any]]


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
        return [SubtitleResult(**result) for result in results]
    except Exception as e:
        logger.error(f"搜索字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/movies/{movie_id}/download-subtitle")
async def download_movie_subtitle(movie_id: int, subtitle_id: str):
    """下载电影字幕"""
    try:
        result = await subtitle_manager.download_movie_subtitle(movie_id, subtitle_id)
        return {"success": True, "message": "字幕下载成功", "data": result}
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
        results = await subtitle_manager.search_episode_subtitles(episode_id)
        return [SubtitleResult(**result) for result in results]
    except Exception as e:
        logger.error(f"搜索字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/episodes/{episode_id}/download-subtitle")
async def download_episode_subtitle(episode_id: str, subtitle_id: str):
    """下载剧集字幕"""
    try:
        result = await subtitle_manager.download_episode_subtitle(episode_id, subtitle_id)
        return {"success": True, "message": "字幕下载成功", "data": result}
    except Exception as e:
        logger.error(f"下载字幕失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- 批量上传字幕 --------------------

@app.post("/api/batch-upload-subtitles")
async def batch_upload_subtitles(
    showId: int = Form(...),
    seasonNumber: int = Form(...),
    files: List[UploadFile] = File(...),
    matches: str = Form(...)  # JSON 字符串
):
    """批量上传字幕文件"""
    try:
        import json
        matches_data = json.loads(matches)
        
        results = []
        for match in matches_data:
            file_index = match.get('fileIndex')
            episode_id = match.get('episodeId')
            
            if file_index is not None and file_index < len(files):
                file = files[file_index]
                result = await subtitle_manager.upload_subtitle(
                    show_id=showId,
                    season_number=seasonNumber,
                    episode_id=episode_id,
                    subtitle_file=file
                )
                results.append(result)
        
        return {
            "success": True,
            "message": f"成功上传 {len(results)} 个字幕",
            "data": results
        }
    except Exception as e:
        logger.error(f"批量上传字幕失败: {e}")
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
        "api_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()
