import asyncio
import gzip
import hashlib
import io
import random
from typing import Dict, List

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from . import BaseSubtitleSource, SubtitleResult


class AssrtSource(BaseSubtitleSource):
    """Assrt subtitle source."""

    def __init__(self):
        super().__init__("Assrt")
        self.base_url = "https://assrt.net"
        self.search_url = f"{self.base_url}/sub/"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://assrt.net/",
        }

    def _minimum_score(self, video_info: dict) -> float:
        if video_info.get("season") and video_info.get("episode"):
            return 0.52
        return 0.48

    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """Search subtitles."""
        results: List[SubtitleResult] = []
        search_terms = self.get_search_terms(video_info)[:6]
        minimum_score = self._minimum_score(video_info)
        logger.info(f"Assrt search terms: {search_terms}")

        try:
            await asyncio.sleep(random.uniform(0.2, 0.6))
            async with aiohttp.ClientSession(headers=self.headers) as session:
                collected: Dict[str, Dict[str, str]] = {}

                for search_term in search_terms:
                    params = {"searchword": search_term, "page": 1}
                    logger.info(f"Assrt searching: {search_term}")

                    async with session.get(self.search_url, params=params, timeout=15) as response:
                        logger.info(f"Assrt status: {response.status}")
                        if response.status == 429:
                            logger.warning("Assrt rate limited")
                            break
                        if response.status != 200:
                            logger.warning(f"Assrt search failed: {response.status}")
                            continue

                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        result_items = soup.find_all("div", class_="subitem")
                        logger.info(f"Assrt found {len(result_items)} raw items")

                        for item in result_items:
                            title_elem = item.find("a", class_="introtitle")
                            if not title_elem:
                                continue

                            title = title_elem.get_text(strip=True)
                            detail_url = title_elem.get("href", "")
                            if detail_url and not detail_url.startswith("http"):
                                detail_url = self.base_url + detail_url
                            if not title or not detail_url or detail_url in collected:
                                continue

                            language = "zh-cn"
                            lang_elem = item.find("span", class_="lang")
                            if lang_elem:
                                lang_text = lang_elem.get_text(strip=True)
                                if "繁" in lang_text:
                                    language = "zh-tw"
                                elif "英" in lang_text:
                                    language = "en"

                            collected[detail_url] = {
                                "title": title,
                                "language": language,
                            }

                        if len(collected) >= 16:
                            break

                for detail_url, item in list(collected.items())[:16]:
                    title = item["title"]
                    score = self.score_candidate(title, video_info, base_score=0.30)
                    if score < minimum_score:
                        logger.debug(
                            f"Assrt skip weak match: {title} ({score:.2f} < {minimum_score:.2f})"
                        )
                        continue

                    subtitle_id = hashlib.md5(
                        f"{self.name}_{detail_url}".encode()
                    ).hexdigest()[:12]

                    results.append(
                        SubtitleResult(
                            id=subtitle_id,
                            source=self.name,
                            title=title,
                            language=item["language"],
                            download_url=detail_url,
                            score=score,
                            file_format="srt",
                        )
                    )
        except asyncio.TimeoutError:
            logger.warning("Assrt search timed out")
        except Exception as exc:
            logger.error(f"Assrt search error: {exc}")

        results.sort(key=lambda result: result.score, reverse=True)
        logger.info(f"Assrt returning {len(results)} results")
        return results

    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool | str:
        """Download a subtitle file from Assrt."""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(subtitle_result.download_url, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Assrt detail page failed: {response.status}")
                        return False

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    download_url = None

                    # Try to find download link by href containing .zip or download path
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        if ".zip" in href.lower() or ("/download/" in href.lower()):
                            download_url = href
                            break

                    # Fallback: look for btn-download class
                    if not download_url:
                        download_btn = soup.find("a", class_="btn-download")
                        if download_btn:
                            download_url = download_btn.get("href")

                    # Fallback: look for link text containing download-related keywords
                    if not download_url:
                        for link in soup.find_all("a"):
                            text = link.get_text(strip=True)
                            if any(kw in text for kw in ["下载字幕", "立即下载", "Download", "下载"]) and link.get("href"):
                                href = link["href"]
                                if "/download/" in href or href.endswith(".zip"):
                                    download_url = href
                                    break

                    if not download_url:
                        logger.error("Assrt download link not found in HTML (url=%s)", subtitle_result.download_url)
                        return False

                    if not download_url.startswith("http"):
                        download_url = self.base_url + download_url

                async with session.get(download_url, timeout=30) as file_response:
                    if file_response.status != 200:
                        logger.error(f"Assrt file download failed: {file_response.status}")
                        return False

                    content = await file_response.read()

                    # Assrt returns XML file containing gzip-compressed subtitle data
                    # Try to detect and decompress gzip content inside
                    if content[:2] == b"\x1f\x8b":
                        logger.info("Assrt: detected gzip content, decompressing")
                        try:
                            content = gzip.GzipFile(fileobj=io.BytesIO(content)).read()
                        except Exception as exc:
                            logger.error(f"Assrt gzip decompress failed: {exc}")
                            return False

                    saved_path = await self._save_download_content(
                        content,
                        save_path,
                        file_url=download_url,
                        preferred_format=subtitle_result.file_format,
                    )
                    if saved_path:
                        logger.info(f"Subtitle downloaded: {saved_path}")
                        return saved_path
                    logger.error("Assrt subtitle save failed")
                    return False
        except asyncio.TimeoutError:
            logger.error("Assrt download timed out")
        except Exception as exc:
            logger.error(f"Assrt download error: {exc}")

        return False
