import aiohttp
import aiofiles
from typing import List
from loguru import logger

from . import BaseSubtitleSource, SubtitleResult
from config import settings


class OpenSubtitlesSource(BaseSubtitleSource):
    """OpenSubtitles 字幕源"""
    
    def __init__(self):
        super().__init__("OpenSubtitles")
        self.api_url = "https://api.opensubtitles.com/api/v1"
        self.api_key = settings.OPENSUBTITLES_API_KEY
        self.token = None
    
    async def _login(self) -> bool:
        """登录获取 token"""
        if not self.api_key or not settings.OPENSUBTITLES_USERNAME:
            logger.warning("OpenSubtitles API 密钥或用户名未配置")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json"
                }
                data = {
                    "username": settings.OPENSUBTITLES_USERNAME,
                    "password": settings.OPENSUBTITLES_PASSWORD
                }
                async with session.post(
                    f"{self.api_url}/login",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.token = result.get("token")
                        return True
                    else:
                        logger.error(f"OpenSubtitles 登录失败: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"OpenSubtitles 登录异常: {e}")
            return False
    
    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """搜索字幕"""
        results = []
        
        if not self.api_key:
            logger.warning("OpenSubtitles API 密钥未配置，跳过")
            return results
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json"
                }
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                
                # 构建查询参数
                params = {
                    "languages": "zh-CN,zh-TW,zh-HK,zh",
                    "query": video_info['name']
                }
                
                # 如果是剧集，添加季和集信息
                if video_info.get('season') and video_info.get('episode'):
                    params["season_number"] = video_info['season']
                    params["episode_number"] = video_info['episode']
                
                async with session.get(
                    f"{self.api_url}/subtitles",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        subtitles = data.get("data", [])
                        
                        for sub in subtitles:
                            attributes = sub.get("attributes", {})
                            files = attributes.get("files", [])
                            
                            if files:
                                file_info = files[0]
                                result = SubtitleResult(
                                    source=self.name,
                                    title=attributes.get("release", video_info['name']),
                                    language=attributes.get("language", "zh"),
                                    download_url=file_info.get("file_id", ""),
                                    score=self._calculate_score(attributes, video_info),
                                    file_format=attributes.get("format", "srt")
                                )
                                results.append(result)
                    else:
                        logger.warning(f"OpenSubtitles 搜索失败: {response.status}")
        except Exception as e:
            logger.error(f"OpenSubtitles 搜索异常: {e}")
        
        return results
    
    def _calculate_score(self, attributes: dict, video_info: dict) -> float:
        """计算匹配度评分"""
        score = 0.5  # 基础分
        
        # 检查分辨率匹配
        if video_info.get('resolution'):
            release = attributes.get("release", "").lower()
            if video_info['resolution'].lower() in release:
                score += 0.2
        
        # 检查来源匹配
        if video_info.get('source'):
            release = attributes.get("release", "").lower()
            if video_info['source'].lower() in release:
                score += 0.2
        
        # 根据下载次数调整
        download_count = attributes.get("download_count", 0)
        if download_count > 1000:
            score += 0.1
        
        return min(score, 1.0)
    
    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool:
        """下载字幕"""
        if not self.api_key:
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Api-Key": self.api_key,
                    "Content-Type": "application/json"
                }
                if self.token:
                    headers["Authorization"] = f"Bearer {self.token}"
                
                # 获取下载链接
                async with session.post(
                    f"{self.api_url}/download",
                    headers=headers,
                    json={"file_id": subtitle_result.download_url}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        download_link = data.get("link")
                        
                        if download_link:
                            # 下载文件
                            async with session.get(download_link) as file_response:
                                if file_response.status == 200:
                                    content = await file_response.read()
                                    async with aiofiles.open(save_path, 'wb') as f:
                                        await f.write(content)
                                    logger.info(f"字幕下载成功: {save_path}")
                                    return True
                    else:
                        logger.error(f"获取下载链接失败: {response.status}")
        except Exception as e:
            logger.error(f"下载字幕异常: {e}")
        
        return False
