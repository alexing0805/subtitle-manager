import asyncio
import io
import os
import re
from typing import Dict, List
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from . import BaseSubtitleSource, SubtitleResult


class SubHDSource(BaseSubtitleSource):
    """SubHD subtitle source."""

    RELEASE_TYPE_PATTERNS = (
        "官方字幕",
        "转载精修",
        "原创翻译",
        "本站原创",
        "听译",
        "字幕翻译",
        "官方译本",
    )
    FORMAT_TOKENS = ("SUP", "ASS", "SSA", "SRT", "VTT", "IDX", "SUB")
    SCRIPT_TOKENS = ("简体", "繁体")
    LANGUAGE_TOKENS = ("英语", "英文", "日语", "韩语")
    SUPPORTED_SUBTITLE_EXTENSIONS = (".srt", ".ass", ".ssa", ".vtt", ".smi", ".sami", ".sub", ".idx", ".sup")

    def __init__(self):
        super().__init__("SubHD")
        self.domains = [
            "https://subhd.tv",
            "https://subhdtw.com",
            "https://subhd.cc",
            "https://subhd.me",
        ]
        self.base_url = self.domains[0]
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """Search subtitles directly from SubHD pages."""
        search_terms = self.get_search_terms(video_info)[:6]
        logger.info(f"SubHD search terms: {search_terms}")

        for domain in self.domains:
            try:
                logger.info(f"Trying SubHD domain: {domain}")
                domain_results: Dict[str, SubtitleResult] = {}

                async with aiohttp.ClientSession() as session:
                    for search_term in search_terms:
                        logger.info(f"SubHD searching: {search_term}")
                        search_url = f"{domain}/search/{quote(search_term)}"

                        async with session.get(search_url, headers=self.headers, timeout=10) as response:
                            if response.status != 200:
                                logger.warning(f"SubHD search failed: {response.status}")
                                continue

                            html = await response.text()
                            if html.strip().startswith("{") or '"success":false' in html:
                                logger.warning("SubHD returned an error payload")
                                continue

                            soup = BeautifulSoup(html, "html.parser")
                            subtitle_links = [
                                link
                                for link in soup.find_all("a", href=True)
                                if "/a/" in link.get("href", "")
                            ]
                            logger.info(f"SubHD found {len(subtitle_links)} raw links")

                            deduped_links = {}
                            for link in subtitle_links:
                                href = self._normalize_detail_url(link.get("href", ""), domain)
                                text = link.get_text(strip=True)
                                if not href or not text:
                                    continue
                                if href not in deduped_links or len(text) > len(deduped_links[href].get_text(strip=True)):
                                    deduped_links[href] = link

                            for link in list(deduped_links.values())[:12]:
                                try:
                                    result = self._parse_search_link(link, video_info, domain)
                                except Exception as exc:
                                    logger.debug(f"SubHD parse failed: {exc}")
                                    continue

                                if not result:
                                    continue

                                dedupe_key = self._build_result_dedupe_key(result)
                                existing = domain_results.get(dedupe_key)
                                if existing is None or self._prefer_result(result, existing):
                                    domain_results[dedupe_key] = result

                            if len(domain_results) >= 12:
                                break

                if domain_results:
                    results = sorted(domain_results.values(), key=lambda item: item.score, reverse=True)
                    logger.info(f"SubHD returning {len(results)} results from {domain}")
                    return results
            except Exception as exc:
                logger.warning(f"SubHD ({domain}) search error: {exc}")
                import traceback

                logger.debug(traceback.format_exc())

        logger.info("SubHD returning 0 results")
        return []

    def _parse_search_link(self, link, video_info: dict, domain: str) -> SubtitleResult | None:
        """Parse one search result link."""
        title = link.get_text(strip=True)
        detail_url = self._normalize_detail_url(link.get("href", ""), domain)
        detail_path = link.get("href", "")
        if not title or not detail_path:
            return None

        import hashlib

        subtitle_id = hashlib.md5(f"SubHD_{detail_url}".encode()).hexdigest()[:12]
        result_container = self._find_result_container(link)
        release_type, meta_tags, file_format = self._extract_result_metadata(result_container, title)
        summary_parts = []
        if release_type:
            summary_parts.append(release_type)
        summary_parts.extend(meta_tags)
        summary = " ".join(summary_parts).strip() or None
        score = self._calculate_score(title, video_info)

        return SubtitleResult(
            id=subtitle_id,
            source=self.name,
            title=title,
            language="zh",
            download_url=detail_url,
            score=score,
            file_format=file_format or "srt",
            filename=title,
            summary=summary,
            release_type=release_type,
            meta_tags=meta_tags,
        )

    def _normalize_detail_url(self, href: str, domain: str) -> str:
        """Normalize detail page URLs so duplicates collapse reliably."""
        if not href:
            return ""

        url = urljoin(domain + "/", href)
        parsed = urlsplit(url)
        normalized_path = parsed.path.rstrip("/")
        return urlunsplit((parsed.scheme, parsed.netloc, normalized_path, "", ""))

    def _find_result_container(self, link):
        """Find the nearest search result card container."""
        current = link
        for _ in range(6):
            current = getattr(current, "parent", None)
            if current is None:
                break
            if current.name in {"div", "li", "article"}:
                text = current.get_text(" ", strip=True)
                if text and len(text) < 500 and current.find("img"):
                    return current
        return getattr(link, "parent", None) or link

    def _extract_result_metadata(self, container, title: str) -> tuple[str | None, List[str], str | None]:
        """Extract release type, descriptor tags, and subtitle format from a search card."""
        if container is None:
            return None, [], None

        candidate_texts: List[str] = []
        for element in container.find_all(["span", "small", "em", "strong", "b", "font", "a", "div"]):
            if element is container:
                continue
            if element.name == "a" and "/a/" in (element.get("href") or ""):
                continue

            text = " ".join(element.stripped_strings)
            text = " ".join(text.split())
            if not text or text == title or len(text) > 40:
                continue
            candidate_texts.append(text)

        combined_text = " ".join(candidate_texts)
        normalized_text = re.sub(r"\s+", "", combined_text)
        release_type = None
        meta_tags: List[str] = []
        file_format = None

        for release_label in self.RELEASE_TYPE_PATTERNS:
            if release_label in normalized_text:
                release_type = release_label
                break

        if "双语" in normalized_text or "中英双语" in normalized_text:
            meta_tags.append("双语")

        script = next((token for token in self.SCRIPT_TOKENS if token in normalized_text), None)
        language = next((token for token in self.LANGUAGE_TOKENS if token in normalized_text), None)
        normalized_language = "英语" if language in {"英语", "英文"} else language

        if script and normalized_language:
            meta_tags.append(f"{script}{normalized_language}")
        else:
            if script:
                meta_tags.append(script)
            if normalized_language:
                meta_tags.append(normalized_language)

        for token in self.FORMAT_TOKENS:
            if token in normalized_text.upper():
                meta_tags.append(token)
                file_format = token.lower()
                break

        if not release_type:
            for text in candidate_texts:
                for release_label in self.RELEASE_TYPE_PATTERNS:
                    if release_label in text:
                        release_type = release_label
                        break
                if release_type:
                    break

        return release_type, meta_tags, file_format

    def _build_result_dedupe_key(self, result: SubtitleResult) -> str:
        """Collapse SubHD duplicates by semantic content rather than raw URL."""
        title_key = self._semantic_key(result.title)
        meta_key = self._semantic_key(" ".join([result.release_type or "", *result.meta_tags, result.file_format or ""]))
        return f"{title_key}|{meta_key}"

    def _semantic_key(self, text: str) -> str:
        return "".join(ch for ch in (text or "").lower() if ch.isalnum())

    def _prefer_result(self, candidate: SubtitleResult, existing: SubtitleResult) -> bool:
        """Choose the richer result when two cards collapse to the same semantic key."""
        candidate_meta_score = len(candidate.meta_tags) + (1 if candidate.release_type else 0)
        existing_meta_score = len(existing.meta_tags) + (1 if existing.release_type else 0)
        if candidate_meta_score != existing_meta_score:
            return candidate_meta_score > existing_meta_score
        return candidate.score > existing.score

    def _calculate_score(self, title: str, video_info: dict) -> float:
        return self.score_candidate(title, video_info, base_score=0.35)

    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool | str:
        """Download subtitles using the SubHD download API."""
        try:
            detail_url = subtitle_result.download_url
            domain = detail_url.split("/a/")[0]
            detail_id = detail_url.split("/a/")[-1]
            down_url = f"{domain}/down/{detail_id}"
            logger.info(f"Starting SubHD download: {detail_url}")

            headers = dict(self.headers)
            headers["Referer"] = domain + "/"

            async with aiohttp.ClientSession() as session:
                async with session.get(detail_url, headers=headers, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"SubHD detail page failed: {response.status}")
                        return False
                    detail_html = await response.text()

                soup = BeautifulSoup(detail_html, "html.parser")
                down_btn = soup.find("a", class_="down")
                if not down_btn:
                    for anchor in soup.find_all("a", href=True):
                        if "/down/" in anchor["href"]:
                            down_btn = anchor
                            break
                if not down_btn:
                    logger.warning("SubHD download button not found")
                    return False

                down_url = down_btn["href"]
                if not down_url.startswith("http"):
                    down_url = domain + down_url

                logger.info(f"Opening SubHD download page: {down_url}")
                headers["Referer"] = detail_url
                async with session.get(down_url, headers=headers, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"SubHD download page failed: {response.status}")
                        return False
                    await response.text()

                api_url = f"{domain}/api/sub/down"
                sid = down_url.split("/")[-1]
                payload = {"sid": sid, "cap": ""}
                headers["Content-Type"] = "application/json"
                headers["Referer"] = down_url
                headers["Accept"] = "application/json"

                logger.info(f"Calling SubHD API: {api_url}, sid={sid}")
                async with session.post(api_url, json=payload, headers=headers, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"SubHD API failed: {response.status}")
                        return False
                    data = await response.json()

                logger.info(f"SubHD API response: {data}")

                if data.get("pass") is False:
                    svg = data.get("msg")
                    if not svg:
                        logger.warning("SubHD captcha challenge missing")
                        return False

                    logger.info("Solving SubHD captcha...")
                    code = await self._solve_captcha(svg)
                    if not code:
                        logger.warning("SubHD captcha solve failed")
                        return False

                    payload["cap"] = code
                    async with session.post(api_url, json=payload, headers=headers, timeout=15) as response:
                        data = await response.json()
                    logger.info(f"SubHD captcha retry response: {data}")

                if not data.get("success"):
                    logger.warning(f"SubHD download failed: {data}")
                    return False

                file_url = data.get("url")
                if not file_url:
                    logger.warning("SubHD file URL missing")
                    return False

                if not file_url.startswith("http"):
                    file_url = domain + file_url

                logger.info(f"Downloading subtitle file: {file_url}")
                headers["Accept"] = "*/*"
                async with session.get(file_url, headers=headers, timeout=60) as response:
                    if response.status != 200:
                        logger.warning(f"SubHD file download failed: {response.status}")
                        return False
                    content = await response.read()

                if len(content) < 100:
                    logger.warning(f"SubHD content too small: {len(content)} bytes")
                    return False

                return await self._save_subtitle(content, save_path, file_url=file_url)
        except Exception as exc:
            logger.error(f"SubHD download error: {exc}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    async def _solve_captcha(self, svg_content: str) -> str | None:
        """Solve the SubHD captcha challenge."""
        try:
            from .captcha_solver import SubHDSolver

            solver = SubHDSolver()
            return solver.solve(svg_content)
        except Exception as exc:
            logger.error(f"Captcha solver error: {exc}")
            return None

    def _resolve_save_path(self, save_path: str, extension: str) -> str:
        """Replace the requested extension with the detected subtitle extension."""
        base_path, _ = os.path.splitext(save_path)
        normalized_extension = extension.lower()
        if not normalized_extension.startswith("."):
            normalized_extension = f".{normalized_extension}"
        return base_path + normalized_extension

    def _detect_subtitle_extension(self, content: bytes, file_url: str | None = None) -> str:
        """Infer subtitle format from the download URL or file signature."""
        if file_url:
            url_path = file_url.split("?", 1)[0].lower()
            _, ext = os.path.splitext(url_path)
            if ext in [".srt", ".ass", ".ssa", ".vtt", ".smi", ".sami", ".sub", ".idx", ".sup", ".zip", ".rar", ".7z"]:
                return ext

        if content[:6] == b"7z\xbc\xaf'\x1c":
            return ".7z"
        if content[:2] == b"PK":
            return ".zip"
        if content[:4] == b"Rar!":
            return ".rar"
        if content[:2] == b"PG":
            return ".sup"
        if content[:512].lstrip().lower().startswith(b"<sami") or b"<sync" in content[:4096].lower():
            return ".smi"
        if content.startswith(b"[Script Info]") or b"[V4+ Styles]" in content[:2048]:
            return ".ass"
        if b"-->" in content[:2048]:
            return ".srt"
        return ".srt"

    def _archive_member_score(self, archive_name: str) -> tuple[int, int, str]:
        """Prefer Chinese subtitle members and more usable formats inside archives."""
        normalized = archive_name.replace("\\", "/").split("/")[-1].lower()
        stem, extension = os.path.splitext(normalized)

        format_score = {
            ".srt": 90,
            ".ass": 80,
            ".ssa": 78,
            ".vtt": 72,
            ".smi": 68,
            ".sami": 68,
            ".sup": 55,
            ".idx": 50,
            ".sub": 48,
        }.get(extension, 0)

        chinese_markers = (
            "zh", "zho", "chi", "chs", "cht", "chs&eng",
            "中文", "中字", "中英", "双语", "简体", "繁体", "国配",
        )
        foreign_only_markers = ("eng", "english", "英文", "英语", "jpn", "japanese", "日语", "korean", "韩语")

        language_score = 0
        if any(marker in stem for marker in chinese_markers):
            language_score += 80
        if "双语" in stem or "中英" in stem:
            language_score += 20
        if any(marker in stem for marker in foreign_only_markers) and not any(marker in stem for marker in chinese_markers):
            language_score -= 40

        return (language_score, format_score, normalized)

    def _pick_archive_member(self, names: List[str]) -> str | None:
        """Pick the best subtitle member from a compressed archive."""
        candidates = [
            name for name in names
            if os.path.splitext(name)[1].lower() in self.SUPPORTED_SUBTITLE_EXTENSIONS
        ]
        if not candidates:
            return None
        return max(candidates, key=self._archive_member_score)

    async def _save_archive_member(self, archive, member_name: str, save_path: str) -> str:
        """Extract one member from an archive to the target directory."""
        extension = os.path.splitext(member_name)[1] or ".srt"
        target_path = self._resolve_save_path(save_path, extension)
        async with aiofiles.open(target_path, "wb") as file_obj:
            await file_obj.write(archive.read(member_name))
        logger.info(f"Subtitle saved: {target_path}")
        return target_path

    async def _save_subtitle(self, content: bytes, save_path: str, file_url: str | None = None) -> str | None:
        """Save subtitles using their real format when available."""
        try:
            detected_extension = self._detect_subtitle_extension(content, file_url)

            if detected_extension == ".zip":
                import zipfile

                try:
                    with zipfile.ZipFile(io.BytesIO(content)) as archive:
                        member_name = self._pick_archive_member(archive.namelist())
                        if not member_name:
                            logger.warning("ZIP archive does not contain a supported subtitle file")
                            return None
                        return await self._save_archive_member(archive, member_name, save_path)
                except Exception as exc:
                    logger.error(f"Failed to extract ZIP subtitle: {exc}")
                    return None

            if detected_extension == ".7z":
                import py7zr

                try:
                    with py7zr.SevenZipFile(io.BytesIO(content), mode="r") as archive:
                        names = archive.getnames()
                        member_name = self._pick_archive_member(names)
                        if not member_name:
                            logger.warning("7z archive does not contain a supported subtitle file")
                            return None
                        extracted = archive.read([member_name])
                        member_data = extracted.get(member_name)
                        if member_data is None:
                            logger.warning(f"7z archive member missing after extraction: {member_name}")
                            return None
                        if hasattr(member_data, "read"):
                            member_bytes = member_data.read()
                        else:
                            member_bytes = member_data
                        extension = os.path.splitext(member_name)[1] or ".srt"
                        target_path = self._resolve_save_path(save_path, extension)
                        async with aiofiles.open(target_path, "wb") as file_obj:
                            await file_obj.write(member_bytes)
                        logger.info(f"Subtitle extracted from 7z: {target_path}")
                        return target_path
                except Exception as exc:
                    logger.error(f"Failed to extract 7z subtitle: {exc}")
                    return None

            if detected_extension == ".rar":
                target_path = self._resolve_save_path(save_path, ".rar")
                async with aiofiles.open(target_path, "wb") as file_obj:
                    await file_obj.write(content)
                logger.info(f"RAR archive saved: {target_path}")
                return target_path

            target_path = self._resolve_save_path(save_path, detected_extension)
            async with aiofiles.open(target_path, "wb") as file_obj:
                await file_obj.write(content)
            logger.info(f"Subtitle saved: {target_path}")
            return target_path
        except Exception as exc:
            logger.error(f"Failed to save subtitle file: {exc}")
            return None
