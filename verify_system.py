#!/usr/bin/env python3
"""
字幕管理器系统验证脚本
快速验证系统核心功能
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_result(test_name, success, message=""):
    """打印测试结果"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"  {status}: {test_name}")
    if message:
        print(f"         {message}")

def test_imports():
    """测试模块导入"""
    print_header("测试模块导入")
    
    tests = [
        ("config 模块", "from config import Config, settings"),
        ("utils 模块", "from utils import get_video_files, has_chinese_subtitle, extract_season_episode"),
        ("subtitle_manager 模块", "from subtitle_manager import SubtitleManager"),
        ("watcher 模块", "from watcher import DirectoryWatcher"),
    ]
    
    results = []
    for name, import_stmt in tests:
        try:
            exec(import_stmt)
            print_result(name, True)
            results.append(True)
        except Exception as e:
            print_result(name, False, str(e))
            results.append(False)
    
    return all(results)

def test_config():
    """测试配置"""
    print_header("测试配置")
    
    from config import Config, settings
    
    results = []
    
    # 测试默认配置
    try:
        config = Config()
        assert config.MIN_FILE_SIZE == 100 * 1024 * 1024
        assert config.SCAN_INTERVAL == 30
        assert 'subhd' in config.SUBTITLE_SOURCES
        print_result("默认配置", True)
        results.append(True)
    except Exception as e:
        print_result("默认配置", False, str(e))
        results.append(False)
    
    # 测试 settings 对象
    try:
        assert settings.MIN_FILE_SIZE_MB == 100
        assert settings.AUTO_DOWNLOAD == True
        print_result("Settings 对象", True)
        results.append(True)
    except Exception as e:
        print_result("Settings 对象", False, str(e))
        results.append(False)
    
    return all(results)

def test_utils():
    """测试工具函数"""
    print_header("测试工具函数")
    
    from utils import (
        get_video_files, 
        has_chinese_subtitle, 
        extract_season_episode,
        clean_filename,
        normalize_filename
    )
    
    results = []
    test_dir = tempfile.mkdtemp()
    
    try:
        # 测试 get_video_files
        try:
            Path(test_dir, "test.mkv").touch()
            Path(test_dir, "test.mp4").touch()
            Path(test_dir, "test.txt").touch()
            files = get_video_files(test_dir)
            assert len(files) == 2
            print_result("get_video_files", True)
            results.append(True)
        except Exception as e:
            print_result("get_video_files", False, str(e))
            results.append(False)
        
        # 测试 has_chinese_subtitle
        try:
            movie_dir = Path(test_dir, "movie")
            movie_dir.mkdir()
            Path(movie_dir, "movie.mkv").touch()
            assert not has_chinese_subtitle(str(movie_dir / "movie.mkv"))
            Path(movie_dir, "movie.zh.srt").touch()
            assert has_chinese_subtitle(str(movie_dir / "movie.mkv"))
            print_result("has_chinese_subtitle", True)
            results.append(True)
        except Exception as e:
            print_result("has_chinese_subtitle", False, str(e))
            results.append(False)
        
        # 测试 extract_season_episode
        try:
            assert extract_season_episode("Show.S01E05.mkv") == (1, 5)
            assert extract_season_episode("Show.S02E12.mkv") == (2, 12)
            assert extract_season_episode("Show.mkv") == (None, None)
            print_result("extract_season_episode", True)
            results.append(True)
        except Exception as e:
            print_result("extract_season_episode", False, str(e))
            results.append(False)
        
        # 测试 clean_filename
        try:
            assert clean_filename("Movie.2021.1080p.mkv") == "Movie"
            assert clean_filename("TV.Show.S01E05.mkv") == "TV Show"
            print_result("clean_filename", True)
            results.append(True)
        except Exception as e:
            print_result("clean_filename", False, str(e))
            results.append(False)
        
        # 测试 normalize_filename
        try:
            assert normalize_filename("Movie.2021.mkv") == "movie"
            assert normalize_filename("TV_Show_S01.mkv") == "tvshow"
            print_result("normalize_filename", True)
            results.append(True)
        except Exception as e:
            print_result("normalize_filename", False, str(e))
            results.append(False)
    
    finally:
        shutil.rmtree(test_dir)
    
    return all(results)

def test_subtitle_manager():
    """测试字幕管理器"""
    print_header("测试字幕管理器")
    
    from config import Config
    from subtitle_manager import SubtitleManager
    
    results = []
    test_dir = tempfile.mkdtemp()
    
    try:
        config = Config()
        config.WATCH_DIRS = [test_dir]
        
        # 测试初始化
        try:
            manager = SubtitleManager(config)
            assert manager.config is not None
            assert manager.db is not None
            print_result("初始化", True)
            results.append(True)
        except Exception as e:
            print_result("初始化", False, str(e))
            results.append(False)
        
        # 测试统计信息
        try:
            stats = manager.get_stats()
            assert 'totalMovies' in stats
            assert 'totalTVShows' in stats
            print_result("get_stats", True)
            results.append(True)
        except Exception as e:
            print_result("get_stats", False, str(e))
            results.append(False)
        
        # 测试任务管理
        try:
            task_id = manager.add_task('test', {'data': 'test'})
            assert task_id is not None
            task = manager.get_task(task_id)
            assert task is not None
            print_result("任务管理", True)
            results.append(True)
        except Exception as e:
            print_result("任务管理", False, str(e))
            results.append(False)
    
    finally:
        shutil.rmtree(test_dir)
    
    return all(results)

def test_frontend_structure():
    """测试前端结构"""
    print_header("测试前端结构")
    
    results = []
    web_dir = Path(__file__).parent / "web"
    
    required_files = [
        "package.json",
        "vite.config.js",
        "index.html",
        "src/main.js",
        "src/App.vue",
        "src/router/index.js",
        "src/stores/subtitle.js",
        "src/components/Sidebar.vue",
        "src/views/Dashboard.vue",
        "src/views/Movies.vue",
        "src/views/TVShows.vue",
        "src/views/BatchUpload.vue",
        "src/views/Settings.vue",
    ]
    
    for file in required_files:
        try:
            file_path = web_dir / file
            assert file_path.exists(), f"文件不存在: {file}"
            print_result(f"文件检查: {file}", True)
            results.append(True)
        except Exception as e:
            print_result(f"文件检查: {file}", False, str(e))
            results.append(False)
    
    return all(results)

def test_docker_structure():
    """测试 Docker 配置"""
    print_header("测试 Docker 配置")
    
    results = []
    root_dir = Path(__file__).parent
    
    required_files = [
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        ".env.example",
        "README.md",
    ]
    
    for file in required_files:
        try:
            file_path = root_dir / file
            assert file_path.exists(), f"文件不存在: {file}"
            print_result(f"文件检查: {file}", True)
            results.append(True)
        except Exception as e:
            print_result(f"文件检查: {file}", False, str(e))
            results.append(False)
    
    return all(results)

def main():
    """主函数"""
    print("\n" + "="*60)
    print("  字幕管理器系统验证")
    print("="*60)
    
    all_results = []
    
    # 运行所有测试
    all_results.append(("模块导入", test_imports()))
    all_results.append(("配置", test_config()))
    all_results.append(("工具函数", test_utils()))
    all_results.append(("字幕管理器", test_subtitle_manager()))
    all_results.append(("前端结构", test_frontend_structure()))
    all_results.append(("Docker 配置", test_docker_structure()))
    
    # 打印总结
    print_header("验证总结")
    
    total = len(all_results)
    passed = sum(1 for _, result in all_results if result)
    failed = total - passed
    
    for name, result in all_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print("\n" + "-"*60)
    print(f"  总计: {total} | 通过: {passed} | 失败: {failed}")
    print("="*60)
    
    if failed == 0:
        print("\n  🎉 所有测试通过！系统验证成功。")
        return 0
    else:
        print(f"\n  ⚠️  {failed} 个测试失败，请检查上述错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
