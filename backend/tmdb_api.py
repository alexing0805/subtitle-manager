"""
TMDB API 集成模块
用于获取电影和电视剧的标准化信息，包括 IMDB ID
"""

import aiohttp
from typing import Optional, Dict, Any
from loguru import logger


class TMDBAPI:
    """TMDB API 客户端"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"

    async def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """搜索电影"""
        if not self.api_key:
            logger.debug("TMDB API 密钥未配置，跳过搜索")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "query": title,
                    "language": "zh-CN"
                }
                if year:
                    params["year"] = year

                async with session.get(
                    f"{self.base_url}/search/movie",
                    params=params,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        if results:
                            # 获取第一个结果
                            movie = results[0]
                            # 获取详细信息（包含 IMDB ID）
                            return await self.get_movie_details(movie["id"])
                    else:
                        logger.warning(f"TMDB 搜索失败: {response.status}")
        except Exception as e:
            logger.error(f"TMDB 搜索异常: {e}")

        return None

    async def search_tv(self, title: str, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """搜索电视剧"""
        if not self.api_key:
            logger.debug("TMDB API 密钥未配置，跳过搜索")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "query": title,
                    "language": "zh-CN"
                }
                if year:
                    params["first_air_date_year"] = year

                async with session.get(
                    f"{self.base_url}/search/tv",
                    params=params,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get("results", [])
                        if results:
                            # 获取第一个结果
                            tv_show = results[0]
                            # 获取详细信息（包含 IMDB ID）
                            return await self.get_tv_details(tv_show["id"])
                    else:
                        logger.warning(f"TMDB 搜索失败: {response.status}")
        except Exception as e:
            logger.error(f"TMDB 搜索异常: {e}")

        return None

    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """获取电影详细信息"""
        if not self.api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "language": "zh-CN",
                    "append_to_response": "external_ids"
                }

                async with session.get(
                    f"{self.base_url}/movie/{tmdb_id}",
                    params=params,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "tmdb_id": data.get("id"),
                            "imdb_id": data.get("imdb_id"),
                            "title": data.get("title"),
                            "original_title": data.get("original_title"),
                            "year": data.get("release_date", "")[:4] if data.get("release_date") else None,
                            "overview": data.get("overview"),
                            "poster_path": f"{self.image_base_url}{data.get('poster_path')}" if data.get("poster_path") else None,
                            "genre_ids": data.get("genre_ids", [])
                        }
        except Exception as e:
            logger.error(f"获取电影详情异常: {e}")

        return None

    async def get_tv_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """获取电视剧详细信息"""
        if not self.api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "language": "zh-CN",
                    "append_to_response": "external_ids"
                }

                async with session.get(
                    f"{self.base_url}/tv/{tmdb_id}",
                    params=params,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        external_ids = data.get("external_ids", {})
                        return {
                            "tmdb_id": data.get("id"),
                            "imdb_id": external_ids.get("imdb_id"),
                            "tvdb_id": external_ids.get("tvdb_id"),
                            "title": data.get("name"),
                            "original_title": data.get("original_name"),
                            "year": data.get("first_air_date", "")[:4] if data.get("first_air_date") else None,
                            "overview": data.get("overview"),
                            "poster_path": f"{self.image_base_url}{data.get('poster_path')}" if data.get("poster_path") else None,
                            "genre_ids": data.get("genre_ids", []),
                            "number_of_seasons": data.get("number_of_seasons"),
                            "number_of_episodes": data.get("number_of_episodes")
                        }
        except Exception as e:
            logger.error(f"获取电视剧详情异常: {e}")

        return None

    async def get_episode_details(self, tv_id: int, season: int, episode: int) -> Optional[Dict[str, Any]]:
        """获取剧集详细信息"""
        if not self.api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "api_key": self.api_key,
                    "language": "zh-CN"
                }

                async with session.get(
                    f"{self.base_url}/tv/{tv_id}/season/{season}/episode/{episode}",
                    params=params,
                    timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "episode_number": data.get("episode_number"),
                            "season_number": data.get("season_number"),
                            "name": data.get("name"),
                            "overview": data.get("overview"),
                            "still_path": f"{self.image_base_url}{data.get('still_path')}" if data.get("still_path") else None,
                            "air_date": data.get("air_date")
                        }
        except Exception as e:
            logger.error(f"获取剧集详情异常: {e}")

        return None


# 全局 TMDB API 实例
tmdb_api = TMDBAPI()


def init_tmdb_api(api_key: Optional[str] = None) -> TMDBAPI:
    """初始化 TMDB API"""
    global tmdb_api
    tmdb_api = TMDBAPI(api_key)
    logger.info(f"TMDB API 初始化完成，API密钥: {'已配置' if api_key else '未配置'}")
    return tmdb_api
