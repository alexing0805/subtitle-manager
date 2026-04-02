import io
import os
import re
import time
import asyncio
import unicodedata
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List, Optional, Dict
from contextlib import asynccontextmanager

import aiofiles
from loguru import logger

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


# ==================== 字幕源熔断器 ====================

class CircuitBreaker:
    """
    字幕源熔断器 - 防止连续失败导致服务雪崩
    连续失败 MAX_FAILURES 次后，该源进入 "断开" 状态，HALF_OPEN_WAIT 秒后尝试半开探测
    """

    MAX_FAILURES: int = 3
    HALF_OPEN_WAIT: float = 30.0  # 秒

    def __init__(self, name: str):
        self.name = name
        self._failures: int = 0
        self._last_failure_time: float = 0.0
        self._state: str = "closed"  # closed | open | half_open
        self._lock = asyncio.Lock()

    @property
    def is_open(self) -> bool:
        return self._state == "open"

    @property
    def is_half_open(self) -> bool:
        return self._state == "half_open"

    def record_success(self):
        """记录成功，重置熔断器"""
        self._failures = 0
        self._state = "closed"

    def record_failure(self):
        """记录失败，达到阈值则断开"""
        self._failures += 1
        self._last_failure_time = time.monotonic()
        if self._failures >= self.MAX_FAILURES:
            self._state = "open"

    async def can_proceed(self) -> bool:
        """检查是否可以执行请求"""
        async with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                # 检查是否应该进入半开状态
                if time.monotonic() - self._last_failure_time >= self.HALF_OPEN_WAIT:
                    self._state = "half_open"
                    return True
                return False
            # half_open 状态允许请求通过
            return True

    def __repr__(self):
        return f"CircuitBreaker({self.name}, state={self._state}, failures={self._failures})"


# 全局熔断器实例字典
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(source_name: str) -> CircuitBreaker:
    """获取指定字幕源的熔断器实例"""
    if source_name not in _circuit_breakers:
        _circuit_breakers[source_name] = CircuitBreaker(source_name)
    return _circuit_breakers[source_name]


@asynccontextmanager
async def circuit_breaker_context(source_name: str):
    """
    熔断器上下文管理器，使用方式:
    
        async with circuit_breaker_context("subhd"):
            # 执行 subhd 相关操作
            ...
    """
    breaker = get_circuit_breaker(source_name)
    if not await breaker.can_proceed():
        raise CircuitBreakerOpen(f"字幕源 {source_name} 熔断器已断开，请稍后重试")

    try:
        yield breaker
    except Exception:
        breaker.record_failure()
        raise
    else:
        breaker.record_success()


class CircuitBreakerOpen(Exception):
    """熔断器开启异常"""
    pass


# ==================== 常量 ====================

SEARCH_TERM_LIMIT = 10
DOWNLOADABLE_SUBTITLE_EXTENSIONS = (".srt", ".ass", ".ssa", ".vtt", ".smi", ".sami", ".sub", ".idx", ".sup", ".7z")
COMMON_RELEASE_TAGS = (
    "2160p", "1080p", "720p", "480p", "4k", "8k",
    "web", "webdl", "web-dl", "webrip", "bluray", "bdrip", "brrip", "hdrip", "hdtv",
    "x264", "x265", "h264", "h265", "hevc", "avc", "aac", "flac", "ddp5", "ddp5.1",
    "atvp", "nf", "amzn", "dsnp", "cr", "v2", "v3"
)
SOURCE_PRIORS = {
    "shooter": 0.10,
    "opensubtitles": 0.06,
    "subhd": 0.05,
    "assrt": 0.04,
}
CHINESE_NUMERALS = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


@dataclass
class SubtitleResult:
    """Subtitle search result."""

    id: str
    source: str
    title: str
    language: str
    download_url: str
    score: float
    file_format: str = "srt"
    filename: Optional[str] = None
    summary: Optional[str] = None
    release_type: Optional[str] = None
    meta_tags: List[str] = field(default_factory=list)
    download_count: Optional[int] = None
    votes: Optional[int] = None
    rating: Optional[float] = None


def normalize_release_text(text: str) -> str:
    """Normalize release text for fuzzy matching."""
    if not text:
        return ""

    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = os.path.splitext(normalized)[0]
    normalized = re.sub(r"tmdb-\w+", " ", normalized)
    normalized = re.sub(r"imdb-[\w-]+", " ", normalized)
    normalized = normalized.replace("_", " ").replace(".", " ")
    normalized = re.sub(r"[\[\]\(\)\{\}]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _dedupe_strings(values: List[str]) -> List[str]:
    seen = set()
    result = []
    for value in values:
        normalized = normalize_release_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(value.strip())
    return result


def _cleanup_alias(text: str) -> str:
    if not text:
        return ""

    value = unicodedata.normalize("NFKC", text)
    value = os.path.splitext(value)[0]
    value = re.sub(r"tmdb-\w+", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"imdb-[\w-]+", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"^[\[\(\{][^\]\)\}]+[\]\)\}]\s*", "", value)
    value = re.sub(r"[\[\]\(\)\{\}]+", " ", value)
    value = re.sub(r"[._]+", " ", value)
    value = re.sub(r"\b(?:19|20)\d{2}\b", " ", value)
    value = re.sub(r"[Ss]\d{1,2}[Ee]\d{1,3}.*$", " ", value)
    value = re.sub(r"\b(?:ep?|episode)\s*\d{1,3}\b.*$", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"第\s*\d{1,3}\s*[集话話].*$", " ", value)
    for release_tag in COMMON_RELEASE_TAGS:
        value = re.sub(
            rf"(?<![A-Za-z0-9]){re.escape(release_tag)}(?![A-Za-z0-9])",
            " ",
            value,
            flags=re.IGNORECASE,
        )
    value = re.sub(r"\s+", " ", value).strip(" -_.")
    return value.strip()


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u3400-\u9fff]", text or ""))


def _similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0

    if fuzz is not None:
        return max(
            fuzz.ratio(left, right),
            fuzz.partial_ratio(left, right),
            fuzz.token_set_ratio(left, right),
        ) / 100.0

    return max(
        SequenceMatcher(None, left, right).ratio(),
        SequenceMatcher(None, left.replace(" ", ""), right.replace(" ", "")).ratio(),
    )


def build_title_aliases(video_info: dict) -> List[str]:
    """Build normalized aliases for search and reranking."""
    nfo_info = video_info.get("nfo") or {}
    aliases = []

    for candidate in nfo_info.get("search_names", []):
        cleaned = _cleanup_alias(candidate)
        if cleaned:
            aliases.append(cleaned)

    direct_candidates = [
        nfo_info.get("originaltitle"),
        nfo_info.get("title"),
        video_info.get("tmdb_title"),
        video_info.get("original_title"),
        video_info.get("title"),
        video_info.get("name"),
        video_info.get("filename"),
    ]
    for candidate in direct_candidates:
        cleaned = _cleanup_alias(candidate or "")
        if cleaned:
            aliases.append(cleaned)

    return _dedupe_strings(aliases)


def build_episode_search_tokens(season: Optional[int], episode: Optional[int]) -> List[str]:
    if not season or not episode:
        return []

    tokens = [
        f"S{season:02d}E{episode:02d}",
        f"S{season}E{episode}",
        f"EP{episode:02d}",
        f"E{episode:02d}",
        f"#{episode}",
        f"#{episode:02d}",
        f"第{episode}集",
        f"第{episode:02d}集",
        f"第{episode}话",
        f"第{episode:02d}话",
        f"第{episode}話",
        f"第{episode:02d}話",
    ]
    return _dedupe_strings(tokens)


def build_search_terms(video_info: dict) -> List[str]:
    """Build search terms shared by all sources."""
    aliases = build_title_aliases(video_info)
    year = video_info.get("year") or (video_info.get("nfo") or {}).get("year")
    season = video_info.get("season")
    episode = video_info.get("episode")
    episode_tokens = build_episode_search_tokens(season, episode)

    search_terms = []
    for alias in aliases:
        if season and episode:
            for token in episode_tokens[:4]:
                search_terms.append(f"{alias} {token}")
            if year:
                search_terms.append(f"{alias} {year}")
        elif year:
            search_terms.append(f"{alias} {year}")

        search_terms.append(alias)

        if _contains_cjk(alias) and season and episode:
            search_terms.append(f"{alias} 第{episode}集")

    name = _cleanup_alias(video_info.get("name") or "")
    if name:
        search_terms.append(name)

    return _dedupe_strings(search_terms)[:SEARCH_TERM_LIMIT]


def _extract_explicit_seasons(text: str) -> List[int]:
    values = set()
    patterns = [
        r"\bs(?:eason)?\s*0?(\d{1,2})(?=e\d|\b)",
        r"第\s*0?(\d{1,2})\s*季",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try:
                values.add(int(match))
            except ValueError:
                continue

    for match in re.findall(r"第\s*([一二三四五六七八九十]+)\s*季", text):
        if match in CHINESE_NUMERALS:
            values.add(CHINESE_NUMERALS[match])

    return sorted(values)


def _extract_explicit_episodes(text: str) -> List[int]:
    values = set()
    patterns = [
        r"\bs\d{1,2}e(\d{1,3})\b",
        r"\b(?:ep?|episode)\s*0?(\d{1,3})\b",
        r"#\s*0?(\d{1,3})\b",
        r"第\s*0?(\d{1,3})\s*[集话話]",
        r"\[\s*0?(\d{1,3})\s*\]",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, re.IGNORECASE):
            try:
                values.add(int(match))
            except ValueError:
                continue
    return sorted(values)


def _extract_explicit_years(text: str) -> List[int]:
    values = set()
    for match in re.findall(r"\b(?:19|20)\d{2}\b", text or ""):
        try:
            values.add(int(match))
        except ValueError:
            continue
    return sorted(values)


def _has_pack_indicator(text: str) -> bool:
    pack_patterns = (
        r"全集",
        r"全\d{1,3}集",
        r"\bcomplete\b",
        r"\bbatch\b",
        r"\b合集\b",
        r"\bcollection\b",
        r"#\d{1,3}\s*[~\-]\s*#?\d{1,3}",
        r"\b\d{1,3}\s*[~\-]\s*\d{1,3}\b",
        r"\bseason\s*\d+\b",
    )
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in pack_patterns)


def score_release_title(
    candidate_title: str,
    video_info: dict,
    source_name: Optional[str] = None,
    source_score: float = 0.0,
) -> float:
    """Score a subtitle candidate using shared matching rules."""
    normalized_candidate = normalize_release_text(candidate_title)
    compact_candidate = normalized_candidate.replace(" ", "")
    aliases = build_title_aliases(video_info)
    alias_scores = []
    alias_contains = False

    for alias in aliases:
        normalized_alias = normalize_release_text(alias)
        if not normalized_alias:
            continue
        alias_scores.append(_similarity(normalized_candidate, normalized_alias))
        if normalized_alias in normalized_candidate or normalized_alias.replace(" ", "") in compact_candidate:
            alias_contains = True

    best_alias_score = max(alias_scores, default=0.0)
    score = min(source_score, 1.0) * 0.20
    score += best_alias_score * 0.45
    if alias_contains:
        score += 0.18

    year = str(video_info.get("year") or (video_info.get("nfo") or {}).get("year") or "").strip()
    explicit_years = _extract_explicit_years(candidate_title)
    if year:
        if year in normalized_candidate:
            score += 0.05
        elif explicit_years:
            score -= 0.18

    release_lower = candidate_title.lower()
    if video_info.get("resolution") and video_info["resolution"].lower() in release_lower:
        score += 0.05
    if video_info.get("source") and video_info["source"].lower() in release_lower:
        score += 0.05
    if video_info.get("group") and video_info["group"].lower() in release_lower:
        score += 0.03

    season = video_info.get("season")
    episode = video_info.get("episode")
    if season and episode:
        exact_episode_match = any(
            normalize_release_text(token).replace(" ", "") in compact_candidate
            for token in build_episode_search_tokens(season, episode)
        )
        explicit_seasons = _extract_explicit_seasons(candidate_title)
        explicit_episodes = _extract_explicit_episodes(candidate_title)
        has_pack = _has_pack_indicator(candidate_title)
        has_episode_marker = exact_episode_match or bool(explicit_episodes)

        if exact_episode_match:
            score += 0.28
        elif explicit_episodes:
            score -= 0.26
        else:
            score -= 0.16

        if explicit_seasons and season not in explicit_seasons:
            score -= 0.38
        elif explicit_seasons:
            score += 0.10

        if explicit_episodes and episode not in explicit_episodes:
            score -= 0.55

        # 如果候选明确写了其它集号/季号，就进一步强力降权，避免 S02E06/S01E54 这类结果混入前排
        if explicit_seasons and explicit_episodes and (season not in explicit_seasons or episode not in explicit_episodes):
            score -= 0.30

        # 对于明确标出了错误集号的条目，直接视为弱匹配，尽量让它们在过滤阈值下消失
        if explicit_episodes and episode not in explicit_episodes and exact_episode_match is False:
            score -= 0.25

        if has_pack and not exact_episode_match:
            score -= 0.28

        if re.search(r"\bsp\b|\bspecial\b|\bova\b|\boad\b", candidate_title, re.IGNORECASE):
            score -= 0.18

    if source_name:
        score += SOURCE_PRIORS.get(source_name.lower(), 0.0)

    return max(0.0, min(score, 1.0))


class BaseSubtitleSource(ABC):
    """Base subtitle source."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """Search subtitles."""
        pass

    @abstractmethod
    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool | str:
        """Download a subtitle and return success or the saved path."""
        pass

    def get_search_terms(self, video_info: dict) -> List[str]:
        return build_search_terms(video_info)

    def score_candidate(self, candidate_title: str, video_info: dict, base_score: float = 0.0) -> float:
        return score_release_title(candidate_title, video_info, self.name, base_score)

    def _resolve_save_path(self, save_path: str, extension: str) -> str:
        """Replace the requested extension with the detected subtitle extension."""
        base_path, _ = os.path.splitext(save_path)
        normalized_extension = extension.lower()
        if not normalized_extension.startswith("."):
            normalized_extension = f".{normalized_extension}"
        return base_path + normalized_extension

    def _detect_download_extension(
        self,
        content: bytes,
        file_url: str | None = None,
        preferred_format: str | None = None,
    ) -> str:
        """Infer subtitle format from the download URL, declared format, or file signature."""
        if file_url:
            url_path = file_url.split("?", 1)[0].lower()
            _, ext = os.path.splitext(url_path)
            if ext in DOWNLOADABLE_SUBTITLE_EXTENSIONS + (".zip", ".rar"):
                return ext

        if preferred_format:
            normalized = preferred_format.lower().strip()
            if not normalized.startswith("."):
                normalized = f".{normalized}"
            if normalized in DOWNLOADABLE_SUBTITLE_EXTENSIONS:
                return normalized

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
        simplified_markers = ("简体", "简中", "chs", "sc", "gb", "gbk")
        traditional_markers = ("繁体", "繁中", "cht", "tc", "big5")
        foreign_only_markers = ("eng", "english", "英文", "英语", "jpn", "japanese", "日语", "korean", "韩语")

        language_score = 0
        if any(marker in stem for marker in chinese_markers):
            language_score += 80
        if any(marker in stem for marker in simplified_markers):
            language_score += 40
        if any(marker in stem for marker in traditional_markers):
            language_score -= 10
        if "双语" in stem or "中英" in stem:
            language_score += 15
        if any(marker in stem for marker in foreign_only_markers) and not any(marker in stem for marker in chinese_markers):
            language_score -= 40

        return (language_score, format_score, normalized)

    def _pick_archive_member(self, names: List[str]) -> str | None:
        """Pick the best subtitle member from a compressed archive."""
        candidates = [
            name for name in names
            if os.path.splitext(name)[1].lower() in DOWNLOADABLE_SUBTITLE_EXTENSIONS
        ]
        if not candidates:
            logger.info(f"Archive subtitle candidates: none from {names}")
            return None

        def _priority_bucket(name: str) -> int:
            raw_name = name.replace("\\", "/").split("/")[-1]
            normalized = raw_name.lower()
            bilingual_markers = ("双语", "中英")

            has_simplified = ("简" in raw_name) or ("chs" in normalized)
            has_traditional = ("繁" in raw_name) or ("cht" in normalized)
            has_bilingual = any(marker in raw_name for marker in bilingual_markers)

            if has_simplified and has_bilingual:
                return 4
            if has_simplified:
                return 3
            if has_bilingual and not has_traditional:
                return 2
            if has_traditional:
                return 1
            return 0

        scored = sorted(
            ((name, _priority_bucket(name), self._archive_member_score(name)) for name in candidates),
            key=lambda item: (item[1], item[2]),
            reverse=True,
        )
        logger.info(
            "Archive subtitle candidates: " + ", ".join(
                f"{name}=>bucket={bucket},lang={score[0]},fmt={score[1]}" for name, bucket, score in scored
            )
        )
        selected = scored[0][0]
        logger.info(f"Archive subtitle selected: {selected}")
        return selected

    async def _save_archive_member(self, archive, member_name: str, save_path: str) -> str:
        """Extract one member from an archive to the target directory."""
        extension = os.path.splitext(member_name)[1] or ".srt"
        target_path = self._resolve_save_path(save_path, extension)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        async with aiofiles.open(target_path, "wb") as file_obj:
            await file_obj.write(archive.read(member_name))
        return target_path

    async def _save_download_content(
        self,
        content: bytes,
        save_path: str,
        file_url: str | None = None,
        preferred_format: str | None = None,
    ) -> str | None:
        """Save downloaded bytes using the most accurate subtitle extension."""
        try:
            detected_extension = self._detect_download_extension(
                content,
                file_url=file_url,
                preferred_format=preferred_format,
            )

            if detected_extension == ".zip":
                with zipfile.ZipFile(io.BytesIO(content)) as archive:
                    archive_names = archive.namelist()
                    logger.info(f"ZIP archive members: {archive_names}")
                    member_name = self._pick_archive_member(archive_names)
                    if not member_name:
                        return None
                    return await self._save_archive_member(archive, member_name, save_path)

            if detected_extension == ".7z":
                import shutil
                import tempfile
                import py7zr

                with py7zr.SevenZipFile(io.BytesIO(content), mode="r") as archive:
                    archive_names = archive.getnames()
                    logger.info(f"7z archive members: {archive_names}")
                    member_name = self._pick_archive_member(archive_names)
                    if not member_name:
                        return None
                    with tempfile.TemporaryDirectory(prefix="subtitle-manager-7z-") as tmp_dir:
                        archive.extract(path=tmp_dir, targets=[member_name])
                        extracted_path = os.path.join(tmp_dir, member_name)
                        if not os.path.exists(extracted_path):
                            return None
                        extension = os.path.splitext(member_name)[1] or ".srt"
                        target_path = self._resolve_save_path(save_path, extension)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        shutil.move(extracted_path, target_path)
                        return target_path

            target_path = self._resolve_save_path(save_path, detected_extension)
            async with aiofiles.open(target_path, "wb") as file_obj:
                await file_obj.write(content)
            return target_path
        except Exception:
            return None


from .opensubtitles import OpenSubtitlesSource
from .subhd import SubHDSource
from .shooter import ShooterSource
from .assrt import AssrtSource


AVAILABLE_SOURCES = {
    "opensubtitles": OpenSubtitlesSource,
    "subhd": SubHDSource,
    "shooter": ShooterSource,
    "assrt": AssrtSource,
}


def get_source(name: str) -> Optional[BaseSubtitleSource]:
    """Get a subtitle source instance."""
    source_class = AVAILABLE_SOURCES.get(name.lower())
    if source_class:
        return source_class()
    return None
