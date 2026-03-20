import os
from typing import List

import aiohttp
from loguru import logger

from . import BaseSubtitleSource, SubtitleResult, build_search_terms


def load_env_file(filepath="/app/.env"):
    """Load a dotenv-style file when running inside the container."""
    try:
        with open(filepath, "r", encoding="utf-8") as file_obj:
            for line in file_obj:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value
    except Exception as exc:
        logger.debug(f"Failed to load .env file: {exc}")


class OpenSubtitlesSource(BaseSubtitleSource):
    """OpenSubtitles API source."""

    def __init__(self):
        super().__init__("OpenSubtitles")
        self.api_url = "https://api.opensubtitles.com/api/v1"
        self.api_key = None
        self.token = None
        load_env_file()

    def _load_config(self):
        self.api_key = os.getenv("OPENSUBTITLES_API_KEY")
        self.username = os.getenv("OPENSUBTITLES_USERNAME")
        self.password = os.getenv("OPENSUBTITLES_PASSWORD")

    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """Search subtitles from OpenSubtitles."""
        results: List[SubtitleResult] = []
        self._load_config()
        if not self.api_key:
            logger.warning("OpenSubtitles API key not configured, skipping")
            return results

        search_terms = build_search_terms(video_info)
        query = search_terms[0] if search_terms else video_info.get("name", "")
        logger.info(f"OpenSubtitles query: {query}")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Api-Key": self.api_key,
                    "User-Agent": "SubtitleManager/1.0",
                }
                params = {
                    "languages": "zh-cn,zh-tw",
                    "query": query,
                }

                if video_info.get("imdb_id"):
                    params["imdb_id"] = video_info["imdb_id"]

                if video_info.get("season") and video_info.get("episode"):
                    params["season_number"] = video_info["season"]
                    params["episode_number"] = video_info["episode"]

                logger.info(f"OpenSubtitles params: {params}")
                async with session.get(
                    f"{self.api_url}/subtitles",
                    headers=headers,
                    params=params,
                    timeout=30,
                ) as response:
                    logger.info(f"OpenSubtitles status: {response.status}")
                    if response.status != 200:
                        text = await response.text()
                        logger.warning(f"OpenSubtitles search failed: {response.status}, {text[:200]}")
                        return results

                    data = await response.json()
                    subtitles = data.get("data", [])
                    logger.info(f"OpenSubtitles found {len(subtitles)} raw items")

                    for subtitle in subtitles:
                        try:
                            attributes = subtitle.get("attributes", {})
                            files = attributes.get("files", [])
                            if not files:
                                continue

                            file_info = files[0]
                            title = attributes.get("release") or query
                            results.append(
                                SubtitleResult(
                                    id=subtitle.get("id") or file_info.get("file_id", ""),
                                    source=self.name,
                                    title=title,
                                    language=attributes.get("language", "zh"),
                                    download_url=file_info.get("file_id", ""),
                                    score=self._calculate_score(attributes, video_info),
                                    file_format=attributes.get("format", "srt"),
                                )
                            )
                        except Exception as exc:
                            logger.debug(f"OpenSubtitles item parse failed: {exc}")
        except Exception as exc:
            logger.error(f"OpenSubtitles search error: {exc}")

        results.sort(key=lambda item: item.score, reverse=True)
        logger.info(f"OpenSubtitles returning {len(results)} results")
        return results

    def _calculate_score(self, attributes: dict, video_info: dict) -> float:
        release = attributes.get("release", "")
        base_score = 0.35

        download_count = attributes.get("download_count", 0)
        if download_count > 5000:
            base_score += 0.08
        elif download_count > 1000:
            base_score += 0.05
        elif download_count > 200:
            base_score += 0.03

        return self.score_candidate(release, video_info, base_score=base_score)

    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool | str:
        """Download a subtitle file from OpenSubtitles."""
        self._load_config()
        if not self.api_key:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Api-Key": self.api_key,
                    "User-Agent": "SubtitleManager/1.0",
                }
                payload = {"file_id": subtitle_result.download_url}

                async with session.post(
                    f"{self.api_url}/download",
                    headers=headers,
                    json=payload,
                    timeout=30,
                ) as response:
                    if response.status != 200:
                        text = await response.text()
                        logger.error(f"OpenSubtitles download link failed: {response.status}, {text[:200]}")
                        return False

                    data = await response.json()
                    download_link = data.get("link")
                    if not download_link:
                        logger.error("OpenSubtitles download link missing")
                        return False

                async with session.get(download_link, timeout=30) as file_response:
                    if file_response.status != 200:
                        logger.error(f"OpenSubtitles file download failed: {file_response.status}")
                        return False

                    content = await file_response.read()
                    saved_path = await self._save_download_content(
                        content,
                        save_path,
                        file_url=download_link,
                        preferred_format=subtitle_result.file_format,
                    )
                    if saved_path:
                        logger.info(f"Subtitle downloaded: {saved_path}")
                        return saved_path
                    logger.error("OpenSubtitles subtitle save failed")
                    return False
        except Exception as exc:
            logger.error(f"OpenSubtitles download error: {exc}")

        return False
