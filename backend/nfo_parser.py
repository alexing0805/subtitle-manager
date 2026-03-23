"""
NFO 文件解析模块
用于从 Kodi/XBMC 格式的 NFO 文件中提取电影/剧集信息
"""

import os
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger


class NFOParser:
    """NFO 文件解析器"""

    @staticmethod
    def parse_movie_nfo(nfo_path: str) -> Optional[Dict[str, Any]]:
        """
        解析电影 NFO 文件

        Args:
            nfo_path: NFO 文件路径

        Returns:
            包含电影信息的字典，解析失败返回 None
        """
        if not os.path.exists(nfo_path):
            return None

        try:
            with open(nfo_path, 'r', encoding='utf-8') as f:
                content = f.read()

            info = {
                'title': NFOParser._extract_tag(content, 'title'),
                'originaltitle': NFOParser._extract_tag(content, 'originaltitle'),
                'year': NFOParser._extract_int_tag(content, 'year'),
                'premiered': NFOParser._extract_tag(content, 'premiered'),
                'rating': NFOParser._extract_float_tag(content, 'rating'),
                'mpaa': NFOParser._extract_tag(content, 'mpaa'),
                'plot': NFOParser._extract_tag(content, 'plot'),
                'tagline': NFOParser._extract_tag(content, 'tagline'),
                'runtime': NFOParser._extract_int_tag(content, 'runtime'),
                'tmdbid': NFOParser._extract_tag(content, 'tmdbid'),
                'imdbid': NFOParser._extract_tag(content, 'imdbid'),
                'imdb_id': NFOParser._extract_tag(content, 'imdbid'),  # 别名
                'id': NFOParser._extract_tag(content, 'id'),
                'genres': NFOParser._extract_tags(content, 'genre'),
                'actors': NFOParser._extract_actors(content),
                'poster': NFOParser._extract_tag(content, 'thumb', 'aspect="poster"'),
                'fanart': NFOParser._extract_tag(content, 'thumb', 'aspect="fanart"'),
            }

            # 如果没有中文标题，使用原标题
            if not info['title'] and info['originaltitle']:
                info['title'] = info['originaltitle']

            # 构建搜索用的标准名称
            info['search_names'] = NFOParser._build_search_names(info)

            logger.debug(f"解析 NFO 文件成功: {nfo_path}, TMDB ID: {info.get('tmdbid')}, IMDB ID: {info.get('imdbid')}")
            return info

        except Exception as e:
            logger.error(f"解析 NFO 文件失败: {nfo_path}, 错误: {e}")
            return None

    @staticmethod
    def _extract_tag(content: str, tag: str, attribute: str = '') -> Optional[str]:
        """从 XML 内容中提取标签值"""
        if attribute:
            # 带属性的标签，如 <thumb aspect="poster">
            pattern = f'<{tag}[^>]*{attribute}[^>]*>([^<]+)</{tag}>'
        else:
            pattern = f'<{tag}>([^<]+)</{tag}>'

        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _extract_int_tag(content: str, tag: str) -> Optional[int]:
        """提取整数类型的标签值"""
        value = NFOParser._extract_tag(content, tag)
        if value:
            try:
                return int(value)
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_float_tag(content: str, tag: str) -> Optional[float]:
        """提取浮点数类型的标签值"""
        value = NFOParser._extract_tag(content, tag)
        if value:
            try:
                return float(value)
            except ValueError:
                pass
        return None

    @staticmethod
    def _extract_tags(content: str, tag: str) -> List[str]:
        """提取所有同名标签的值"""
        pattern = f'<{tag}>([^<]+)</{tag}>'
        matches = re.findall(pattern, content, re.IGNORECASE)
        return [m.strip() for m in matches]

    @staticmethod
    def _extract_actors(content: str) -> List[Dict[str, str]]:
        """提取演员信息"""
        actors = []
        # 匹配 <actor>...</actor> 块
        pattern = r'<actor>(.*?)</actor>'
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)

        for match in matches:
            actor = {
                'name': NFOParser._extract_tag(match, 'name') or '',
                'role': NFOParser._extract_tag(match, 'role') or '',
                'thumb': NFOParser._extract_tag(match, 'thumb') or '',
                'tmdbid': NFOParser._extract_tag(match, 'tmdbid') or '',
            }
            if actor['name']:
                actors.append(actor)

        return actors

    @staticmethod
    def _build_search_names(info: Dict[str, Any]) -> List[str]:
        """
        构建用于字幕搜索的名称列表

        优先级：
        1. 原名.年份.TMDB ID.IMDB ID
        2. 中文名.年份
        3. 原名.年份
        """
        search_names = []

        original_title = info.get('originaltitle') or info.get('title', '')
        year = info.get('year')
        tmdb_id = info.get('tmdbid')
        imdb_id = info.get('imdbid') or info.get('imdb_id')
        chinese_title = info.get('title', '')

        # 格式1: 原名.年份.TMDB ID.IMDB ID (最精确)
        if original_title and year and (tmdb_id or imdb_id):
            name_parts = [original_title, str(year)]
            if tmdb_id:
                name_parts.append(f"tmdb-{tmdb_id}")
            if imdb_id:
                name_parts.append(f"imdb-{imdb_id}")
            search_names.append('.'.join(name_parts))

        # 格式2: 原名.年份
        if original_title and year:
            search_names.append(f"{original_title}.{year}")

        # 格式3: 中文名.年份
        if chinese_title and year and chinese_title != original_title:
            search_names.append(f"{chinese_title}.{year}")

        # 格式4: 只有原名
        if original_title:
            search_names.append(original_title)

        # 格式5: 只有中文名
        if chinese_title and chinese_title != original_title:
            search_names.append(chinese_title)

        return search_names

    @staticmethod
    def find_nfo_file(video_path: str) -> Optional[str]:
        """
        查找视频文件对应的 NFO 文件

        电影：优先使用同目录下的 movie.nfo 或 {name}.nfo
        剧集：按以下顺序查找
              1. episode-level NFO（同目录同名.nfo）
              2. series-level NFO（season.nfo / tvshow.nfo）
        """
        video_dir = Path(video_path).parent
        video_name = Path(video_path).stem
        checked_paths = []

        # 判断是否为剧集文件（包含 SxxExx 模式）
        is_tv_episode = bool(re.search(r'[Ss]\d{1,2}[Ee]\d{1,2}', video_name))

        # 剧集：先查 episode-level，再查 series-level
        # 电影：直接用 episode-level（包含movie.nfo）
        candidate_groups = [
            [video_dir / f"{video_name}.nfo", video_dir / "movie.nfo"],
        ]
        if is_tv_episode:
            # 剧集额外查找 series-level NFO
            candidate_groups.append([video_dir / "season.nfo", video_dir / "tvshow.nfo"])
            candidate_groups.append([video_dir.parent / "season.nfo", video_dir.parent / "tvshow.nfo"])
            candidate_groups.append([video_dir.parent.parent / "tvshow.nfo"])

        for candidates in candidate_groups:
            for candidate in candidates:
                candidate_str = str(candidate)
                if candidate_str in checked_paths:
                    continue
                checked_paths.append(candidate_str)
                if candidate.exists():
                    return candidate_str

        return None

    @staticmethod
    def get_video_info_with_nfo(video_path: str) -> Dict[str, Any]:
        """
        获取视频信息，如果存在 NFO 文件则合并 NFO 信息

        Args:
            video_path: 视频文件路径

        Returns:
            合并后的视频信息字典
        """
        from backend.utils import extract_video_info

        # 获取基础视频信息
        info = extract_video_info(video_path)

        # 判断是否为剧集文件
        is_tv_episode = bool(re.search(r'[Ss]\d{1,2}[Ee]\d{1,2}', os.path.basename(video_path)))

        # 电视剧：优先从 series-level NFO（tvshow.nfo）获取 TMDB ID
        # 因为 episode-level NFO 可能包含旧的/错误的 TMDB ID
        # 注意：只有当 series-level NFO 有有效的 tmdbid 时才使用
        series_tmdb_id = None
        if is_tv_episode:
            video_dir = Path(video_path).parent
            series_nfo_paths = [
                video_dir / "tvshow.nfo",
                video_dir.parent / "tvshow.nfo",
                video_dir.parent.parent / "tvshow.nfo",
            ]
            for series_nfo in series_nfo_paths:
                if series_nfo.exists():
                    series_info = NFOParser.parse_movie_nfo(str(series_nfo))
                    if series_info and series_info.get('tmdbid'):
                        # 只有当 tmdbid 看起来是有效的数字时才使用
                        series_tmdbid = str(series_info['tmdbid']).strip()
                        if series_tmdbid.isdigit() and len(series_tmdbid) >= 6:
                            series_tmdb_id = series_tmdbid
                            logger.info(f"从 series-level NFO 获取 TMDB ID: {series_nfo}, TMDB ID: {series_tmdb_id}")
                            break

        # 查找并解析 episode-level NFO（用于其他信息）
        nfo_path = NFOParser.find_nfo_file(video_path)
        if nfo_path:
            nfo_info = NFOParser.parse_movie_nfo(nfo_path)
            if nfo_info:
                # 合并 NFO 信息到基础信息
                info['nfo'] = nfo_info
                info['nfo_path'] = nfo_path

                # TMDB ID：对于 TV 剧集，存储 series-level TMDB ID 用于字幕搜索
                # episode-level NFO 的 TMDB ID 可能是错误的，不用于搜索
                if series_tmdb_id:
                    info['tmdb_id'] = series_tmdb_id
                    info['series_tmdb_id'] = series_tmdb_id

                if nfo_info.get('imdbid') or nfo_info.get('imdb_id'):
                    info['imdb_id'] = nfo_info.get('imdbid') or nfo_info.get('imdb_id')
                if nfo_info.get('originaltitle'):
                    info['original_title'] = nfo_info['originaltitle']
                if nfo_info.get('search_names'):
                    info['search_names'] = nfo_info['search_names']

                logger.info(f"成功加载 NFO 信息: {video_path}, TMDB ID: {info.get('tmdb_id')}")

        return info
