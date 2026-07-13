"""
后端工具函数单元测试
"""
import os
import sys
import tempfile
import pytest

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils import (
    extract_video_info,
    is_movie_file,
    is_tv_episode,
    format_title_for_search,
    clean_filename,
    format_size,
    get_subtitle_save_path,
    is_video_file,
    get_video_files,
)


class TestExtractVideoInfo:
    """extract_video_info 函数的测试"""

    def test_extract_movie_info(self):
        """测试电影文件名解析"""
        info = extract_video_info("/movies/Avatar.2009.1080p.BluRay.x264.mkv")
        assert info['year'] == '2009'
        assert info['resolution'] == '1080p'
        assert info['source'] == 'BluRay'
        assert info['season'] is None
        assert info['episode'] is None

    def test_extract_tv_episode_info(self):
        """测试剧集文件名解析"""
        info = extract_video_info("/tvshows/The.Show.S01E05.720p.WEB-DL.mkv")
        assert info['season'] == 1
        assert info['episode'] == 5
        assert info['resolution'] == '720p'
        assert info['source'] == 'WEB-DL'

    def test_extract_anime_episode(self):
        """测试动漫文件名解析"""
        info = extract_video_info("/anime/Attack.on.Titan.S04E12.1080p.CR.mkv")
        assert info['season'] == 4
        assert info['episode'] == 12

    def test_extract_year_only(self):
        """测试只有年份的情况"""
        info = extract_video_info("/movies/Old.Movie.1999.mkv")
        assert info['year'] == '1999'


class TestIsMovieFile:
    """is_movie_file 函数的测试"""

    def test_movie_file(self):
        """电影文件应返回 True"""
        assert is_movie_file("/movies/Inception.2010.1080p.mkv") is True

    def test_tv_episode_file(self):
        """剧集文件应返回 False"""
        assert is_movie_file("/tvshows/Show.S01E01.mkv") is False

    def test_non_video_file(self):
        """非视频文件应返回 False"""
        assert is_movie_file("/movies/subtitle.srt") is False
        assert is_movie_file("/movies/poster.jpg") is False


class TestIsTvEpisode:
    """is_tv_episode 函数的测试"""

    def test_tv_episode(self):
        """剧集文件应返回 True"""
        assert is_tv_episode("/tvshows/Show.S01E01.mkv") is True

    def test_movie_file(self):
        """电影文件应返回 False"""
        assert is_tv_episode("/movies/Inception.2010.mkv") is False


class TestFormatTitleForSearch:
    """format_title_for_search 函数的测试"""

    def test_remove_year(self):
        """测试移除年份"""
        result = format_title_for_search("Movie.2024.1080p.mkv")
        assert "2024" not in result

    def test_remove_resolution(self):
        """测试移除分辨率"""
        result = format_title_for_search("Movie.2024.1080p.BluRay.mkv")
        assert "1080p" not in result

    def test_basic_cleaning(self):
        """测试基本清理功能"""
        # 验证扩展名被移除，基本的名称清理
        result = format_title_for_search("Movie.Name.2024.1080p.BluRay.mkv")
        assert ".mkv" not in result
        assert "1080p" not in result
        # 验证点被替换为空格
        assert "." not in result


class TestCleanFilename:
    """clean_filename 函数的测试"""

    def test_remove_illegal_chars(self):
        """测试移除非法字符"""
        result = clean_filename('file:name?test*.mkv')
        assert ":" not in result
        assert "?" not in result
        assert "*" not in result

    def test_preserve_valid_chars(self):
        """测试保留有效字符"""
        result = clean_filename("My.Movie.File.2024.mkv")
        assert "My" in result
        assert "Movie" in result
        assert ".mkv" in result


class TestFormatSize:
    """format_size 函数的测试"""

    def test_bytes(self):
        assert format_size(500) == "500.00 B"

    def test_kilobytes(self):
        assert format_size(1024) == "1.00 KB"

    def test_megabytes(self):
        assert format_size(1024 * 1024 * 5) == "5.00 MB"

    def test_gigabytes(self):
        assert format_size(1024 * 1024 * 1024 * 2) == "2.00 GB"


class TestGetSubtitleSavePath:
    """get_subtitle_save_path 函数的测试"""

    def test_plex_format_movie(self):
        """测试 PLEX 格式的电影字幕路径"""
        path = get_subtitle_save_path(
            "/movies/Avatar.2009.1080p.mkv",
            lang_code="zh-cn",
            plex_format=True
        )
        assert path.endswith(".zh-cn.srt")
        assert "Avatar.2009.1080p" in path

    def test_plex_format_tv(self):
        """测试 PLEX 格式的剧集字幕路径"""
        path = get_subtitle_save_path(
            "/tvshows/Show.S01E05.720p.mkv",
            lang_code="zh",
            plex_format=True
        )
        assert path.endswith(".zh.srt")
        assert "S01E05" in path

    def test_standard_format(self):
        """测试标准格式"""
        path = get_subtitle_save_path(
            "/movies/Avatar.mkv",
            lang_code="zh-cn",
            plex_format=False
        )
        assert path.endswith(".zh-cn.srt")


class TestIsVideoFile:
    """is_video_file 函数的测试"""

    def test_supported_formats(self):
        """支持的视频格式"""
        assert is_video_file("movie.mkv") is True
        assert is_video_file("movie.mp4") is True
        assert is_video_file("movie.avi") is True
        assert is_video_file("movie.mov") is True

    def test_unsupported_formats(self):
        """不支持的格式"""
        assert is_video_file("subtitle.srt") is False
        assert is_video_file("image.jpg") is False
        assert is_video_file("document.pdf") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
