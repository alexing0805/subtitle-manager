"""
NFO 解析器和字幕评分逻辑的单元测试
"""
import os
import sys
import tempfile
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.nfo_parser import NFOParser
from backend.subtitle_sources import (
    score_release_title,
    build_title_aliases,
    build_search_terms,
    normalize_release_text,
    SUBTITLE_EXTENSIONS,
    DOWNLOADABLE_SUBTITLE_EXTENSIONS,
)


# ==================== NFO 解析器测试 ====================


class TestNFOParser:
    """NFOParser 类的测试"""

    def test_parse_movie_nfo(self, tmp_path):
        """测试电影 NFO 文件解析"""
        nfo_content = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<movie>
    <title>阿凡达</title>
    <originaltitle>Avatar</originaltitle>
    <year>2009</year>
    <rating>7.8</rating>
    <runtime>162</runtime>
    <tmdbid>19995</tmdbid>
    <imdbid>tt0499549</imdbid>
    <genre>科幻</genre>
    <genre>动作</genre>
</movie>"""
        nfo_file = tmp_path / "movie.nfo"
        nfo_file.write_text(nfo_content, encoding="utf-8")

        info = NFOParser.parse_movie_nfo(str(nfo_file))

        assert info is not None
        assert info["title"] == "阿凡达"
        assert info["originaltitle"] == "Avatar"
        assert info["year"] == 2009
        assert info["rating"] == 7.8
        assert info["runtime"] == 162
        assert info["tmdbid"] == "19995"
        assert info["imdbid"] == "tt0499549"
        assert "科幻" in info["genres"]
        assert "动作" in info["genres"]

    def test_parse_nfo_nonexistent(self):
        """不存在的 NFO 文件"""
        result = NFOParser.parse_movie_nfo("/nonexistent/path.nfo")
        assert result is None

    def test_parse_nfo_missing_fields(self, tmp_path):
        """缺少字段的 NFO 文件"""
        nfo_content = """<movie>
    <title>Test Movie</title>
</movie>"""
        nfo_file = tmp_path / "movie.nfo"
        nfo_file.write_text(nfo_content, encoding="utf-8")

        info = NFOParser.parse_movie_nfo(str(nfo_file))
        assert info is not None
        assert info["title"] == "Test Movie"
        assert info["year"] is None
        assert info["tmdbid"] is None

    def test_find_nfo_file_movie(self, tmp_path):
        """电影 NFO 文件查找"""
        video_file = tmp_path / "Avatar.2009.1080p.mkv"
        video_file.touch()
        nfo_file = tmp_path / "Avatar.2009.1080p.nfo"
        nfo_file.write_text("<movie><title>Avatar</title></movie>", encoding="utf-8")

        result = NFOParser.find_nfo_file(str(video_file))
        assert result is not None
        assert "Avatar.2009.1080p.nfo" in result

    def test_find_nfo_file_movie_general(self, tmp_path):
        """通用 movie.nfo 查找"""
        video_file = tmp_path / "Avatar.mkv"
        video_file.touch()
        nfo_file = tmp_path / "movie.nfo"
        nfo_file.write_text("<movie><title>Avatar</title></movie>", encoding="utf-8")

        result = NFOParser.find_nfo_file(str(video_file))
        assert result is not None
        assert "movie.nfo" in result

    def test_build_search_names(self):
        """测试搜索名称构建"""
        info = {
            "title": "阿凡达",
            "originaltitle": "Avatar",
            "year": 2009,
            "tmdbid": "19995",
            "imdbid": "tt0499549",
        }
        names = NFOParser._build_search_names(info)
        assert len(names) > 0
        assert any("Avatar" in name for name in names)
        assert any("19995" in name for name in names)


# ==================== 字幕评分逻辑测试 ====================


class TestScoreReleaseTitle:
    """score_release_title 函数的测试"""

    def _make_video_info(self, **kwargs):
        defaults = {
            "title": "Avatar",
            "original_title": "Avatar",
            "year": "2009",
            "resolution": "1080p",
            "season": None,
            "episode": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_exact_title_match_scores_high(self):
        """标题精确匹配应得高分"""
        video_info = self._make_video_info()
        score = score_release_title("Avatar 2009 1080p BluRay", video_info)
        assert score > 0.5

    def test_wrong_title_scores_low(self):
        """不匹配的标题应得低分"""
        video_info = self._make_video_info()
        score = score_release_title("Inception 2010 720p WEB-DL", video_info)
        assert score < 0.4

    def test_episode_match(self):
        """正确集号应加分"""
        video_info = self._make_video_info(
            title="Breaking Bad", season=1, episode=3
        )
        correct = score_release_title("Breaking Bad S01E03 720p", video_info)
        wrong = score_release_title("Breaking Bad S01E05 720p", video_info)
        assert correct > wrong

    def test_year_match_bonus(self):
        """年份匹配应加分"""
        video_info = self._make_video_info()
        with_year = score_release_title("Avatar 2009", video_info)
        without_year = score_release_title("Avatar", video_info)
        assert with_year >= without_year


class TestBuildTitleAliases:
    """build_title_aliases 函数的测试"""

    def test_builds_aliases_from_nfo(self):
        """从 NFO 信息构建别名"""
        video_info = {
            "nfo": {
                "originaltitle": "Avatar",
                "title": "阿凡达",
                "search_names": ["Avatar.2009"],
            },
            "title": "Avatar",
        }
        aliases = build_title_aliases(video_info)
        assert len(aliases) > 0

    def test_builds_aliases_without_nfo(self):
        """没有 NFO 信息时的别名构建"""
        video_info = {"title": "Avatar", "name": "Avatar.2009.1080p.mkv"}
        aliases = build_title_aliases(video_info)
        assert len(aliases) > 0


class TestNormalizeReleaseText:
    """normalize_release_text 函数的测试"""

    def test_basic_normalization(self):
        """基本文本规范化"""
        result = normalize_release_text("Avatar.2009.1080p.BluRay.x264")
        assert "." not in result
        assert result == result.lower()

    def test_empty_string(self):
        """空字符串"""
        assert normalize_release_text("") == ""
        assert normalize_release_text(None) == ""


# ==================== 常量一致性测试 ====================


class TestConstants:
    """测试常量定义的一致性"""

    def test_subtitle_extensions_subset(self):
        """SUBTITLE_EXTENSIONS 应是 DOWNLOADABLE_SUBTITLE_EXTENSIONS 的子集"""
        for ext in SUBTITLE_EXTENSIONS:
            assert ext in DOWNLOADABLE_SUBTITLE_EXTENSIONS

    def test_downloadable_includes_7z(self):
        """DOWNLOADABLE_SUBTITLE_EXTENSIONS 应包含 .7z"""
        assert ".7z" in DOWNLOADABLE_SUBTITLE_EXTENSIONS

    def test_all_extensions_start_with_dot(self):
        """所有扩展名应以点开头"""
        for ext in SUBTITLE_EXTENSIONS:
            assert ext.startswith(".")
        for ext in DOWNLOADABLE_SUBTITLE_EXTENSIONS:
            assert ext.startswith(".")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
