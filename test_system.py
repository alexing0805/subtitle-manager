#!/usr/bin/env python3
"""
字幕管理器系统测试
测试所有核心功能和 API 接口
"""

import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from utils import (
    get_video_files, 
    has_chinese_subtitle, 
    extract_season_episode,
    clean_filename,
    normalize_filename
)
from subtitle_manager import SubtitleManager


class TestConfig(unittest.TestCase):
    """测试配置模块"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        self.assertEqual(config.MIN_FILE_SIZE, 50 * 1024 * 1024)
        self.assertEqual(config.SCAN_INTERVAL, 3600)
        self.assertIn('subhd', config.SUBTITLE_SOURCES)
        self.assertIn('zimuku', config.SUBTITLE_SOURCES)
    
    def test_env_override(self):
        """测试环境变量覆盖"""
        os.environ['SUBTITLE_MIN_FILE_SIZE'] = '100'
        os.environ['SUBTITLE_SCAN_INTERVAL'] = '1800'
        
        config = Config()
        self.assertEqual(config.MIN_FILE_SIZE, 100 * 1024 * 1024)
        self.assertEqual(config.SCAN_INTERVAL, 1800)
        
        # 清理环境变量
        del os.environ['SUBTITLE_MIN_FILE_SIZE']
        del os.environ['SUBTITLE_SCAN_INTERVAL']


class TestUtils(unittest.TestCase):
    """测试工具函数"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.test_dir)
    
    def test_get_video_files(self):
        """测试获取视频文件"""
        # 创建测试文件
        video_files = ['test1.mkv', 'test2.mp4', 'test3.avi', 'test.txt']
        for f in video_files:
            Path(self.test_dir, f).touch()
        
        result = get_video_files(self.test_dir)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(f.endswith(('.mkv', '.mp4', '.avi')) for f in result))
    
    def test_has_chinese_subtitle(self):
        """测试中文字幕检测"""
        # 创建带字幕的视频目录
        video_dir = Path(self.test_dir, 'movie')
        video_dir.mkdir()
        
        # 创建视频文件
        Path(video_dir, 'movie.mkv').touch()
        
        # 无字幕
        self.assertFalse(has_chinese_subtitle(str(video_dir / 'movie.mkv')))
        
        # 创建中文字幕文件
        Path(video_dir, 'movie.zh.srt').touch()
        self.assertTrue(has_chinese_subtitle(str(video_dir / 'movie.mkv')))
        
        # 创建英文字幕文件
        Path(video_dir, 'movie.en.srt').touch()
        # 应该仍然返回 True，因为有中文字幕
        self.assertTrue(has_chinese_subtitle(str(video_dir / 'movie.mkv')))
    
    def test_extract_season_episode(self):
        """测试季集号提取"""
        test_cases = [
            ('Show.S01E05.mkv', (1, 5)),
            ('Show.S02E12.1080p.mkv', (2, 12)),
            ('Show.1x05.mkv', (1, 5)),
            ('Show.S01E05E06.mkv', (1, 5)),
            ('Show.mkv', (None, None)),
        ]
        
        for filename, expected in test_cases:
            result = extract_season_episode(filename)
            self.assertEqual(result, expected, f"Failed for {filename}")
    
    def test_clean_filename(self):
        """测试文件名清理"""
        test_cases = [
            ('Movie.2021.1080p.BluRay.x264.mkv', 'Movie'),
            ('TV.Show.S01E05.720p.WEB-DL.mkv', 'TV Show'),
            ('Movie.2021.mkv', 'Movie'),
        ]
        
        for filename, expected in test_cases:
            result = clean_filename(filename)
            self.assertEqual(result, expected, f"Failed for {filename}")
    
    def test_normalize_filename(self):
        """测试文件名标准化"""
        test_cases = [
            ('Movie.2021.1080p.BluRay.x264.mkv', 'movie'),
            ('TV.Show.S01E05.720p.WEB-DL.mkv', 'tvshow'),
            ('Movie_2021.mkv', 'movie'),
        ]
        
        for filename, expected in test_cases:
            result = normalize_filename(filename)
            self.assertEqual(result, expected, f"Failed for {filename}")


class TestSubtitleManager(unittest.TestCase):
    """测试字幕管理器"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.config = Config()
        self.config.WATCH_DIRS = [self.test_dir]
        self.manager = SubtitleManager(self.config)
    
    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.manager.config)
        self.assertIsNotNone(self.manager.db)
        self.assertEqual(len(self.manager.subtitle_sources), 3)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        stats = self.manager.get_stats()
        
        self.assertIn('totalMovies', stats)
        self.assertIn('moviesWithSubtitle', stats)
        self.assertIn('moviesWithoutSubtitle', stats)
        self.assertIn('totalTVShows', stats)
        self.assertIn('totalEpisodes', stats)
        self.assertIn('episodesWithSubtitle', stats)
        self.assertIn('episodesWithoutSubtitle', stats)
        self.assertIn('recentDownloads', stats)
        self.assertIn('pendingTasks', stats)
    
    @patch('subtitle_manager.SubtitleManager._scan_directory')
    def test_scan_library(self, mock_scan):
        """测试扫描库"""
        mock_scan.return_value = None
        
        asyncio.run(self.manager.scan_library())
        
        # 验证扫描被调用
        self.assertTrue(mock_scan.called)
    
    def test_task_management(self):
        """测试任务管理"""
        # 添加任务
        task_id = self.manager.add_task('test_task', {'test': 'data'})
        self.assertIsNotNone(task_id)
        
        # 获取任务
        task = self.manager.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task['type'], 'test_task')
        
        # 更新任务状态
        self.manager.update_task_status(task_id, 'completed', result={'success': True})
        task = self.manager.get_task(task_id)
        self.assertEqual(task['status'], 'completed')
        
        # 获取所有任务
        tasks = self.manager.get_tasks()
        self.assertEqual(len(tasks), 1)
        
        # 取消任务
        self.manager.cancel_task(task_id)
        task = self.manager.get_task(task_id)
        self.assertEqual(task['status'], 'cancelled')


class TestAPIEndpoints(unittest.TestCase):
    """测试 API 端点（需要 FastAPI 测试客户端）"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        try:
            from fastapi.testclient import TestClient
            from api_server import app
            cls.client = TestClient(app)
            cls.api_available = True
        except ImportError:
            cls.api_available = False
    
    def test_health_check(self):
        """测试健康检查端点"""
        if not self.api_available:
            self.skipTest("FastAPI 测试客户端不可用")
        
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_root_endpoint(self):
        """测试根端点"""
        if not self.api_available:
            self.skipTest("FastAPI 测试客户端不可用")
        
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('version', data)
    
    def test_get_stats(self):
        """测试获取统计信息端点"""
        if not self.api_available:
            self.skipTest("FastAPI 测试客户端不可用")
        
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('totalMovies', data)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
        
        # 创建测试目录结构
        self.movies_dir = Path(self.test_dir, 'movies')
        self.tvshows_dir = Path(self.test_dir, 'tvshows')
        self.movies_dir.mkdir()
        self.tvshows_dir.mkdir()
        
        # 创建测试电影
        movie_dir = self.movies_dir / 'Test Movie (2021)'
        movie_dir.mkdir()
        (movie_dir / 'Test.Movie.2021.1080p.mkv').touch()
        
        # 创建测试电视剧
        show_dir = self.tvshows_dir / 'Test Show'
        show_dir.mkdir()
        season_dir = show_dir / 'Season 01'
        season_dir.mkdir()
        (season_dir / 'Test.Show.S01E01.mkv').touch()
        (season_dir / 'Test.Show.S01E02.mkv').touch()
    
    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        config = Config()
        config.WATCH_DIRS = [str(self.movies_dir), str(self.tvshows_dir)]
        
        manager = SubtitleManager(config)
        
        # 1. 扫描库
        asyncio.run(manager.scan_library())
        
        # 2. 获取统计信息
        stats = manager.get_stats()
        self.assertGreaterEqual(stats['totalMovies'], 0)
        self.assertGreaterEqual(stats['totalTVShows'], 0)
        
        # 3. 获取电影列表
        movies = manager.get_movies()
        self.assertIsInstance(movies, list)
        
        # 4. 获取电视剧列表
        shows = manager.get_tvshows()
        self.assertIsInstance(shows, list)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestUtils))
    suite.addTests(loader.loadTestsFromTestCase(TestSubtitleManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
