#!/usr/bin/env python3
"""
字幕管理器本地测试脚本
在不使用 Docker 的情况下测试系统功能
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
import subprocess
import time
import json

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

def print_header(text):
    """打印标题"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text):
    """打印成功信息"""
    print(f"  ✓ {text}")

def print_error(text):
    """打印错误信息"""
    print(f"  ✗ {text}")

def print_info(text):
    """打印信息"""
    print(f"  ℹ {text}")

def test_python_environment():
    """测试 Python 环境"""
    print_header("测试 Python 环境")
    
    try:
        import python
        print_success(f"Python 版本: {sys.version}")
        return True
    except:
        print_error("无法获取 Python 版本")
        return False

def test_imports():
    """测试模块导入"""
    print_header("测试模块导入")
    
    modules = [
        ("config", "from config import Config, settings"),
        ("utils", "from utils import get_video_files, has_chinese_subtitle, extract_season_episode"),
        ("subtitle_manager", "from subtitle_manager import SubtitleManager"),
    ]
    
    results = []
    for name, import_stmt in modules:
        try:
            exec(import_stmt)
            print_success(f"{name} 模块导入成功")
            results.append(True)
        except Exception as e:
            print_error(f"{name} 模块导入失败: {e}")
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
            print_success("get_video_files 测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"get_video_files 测试失败: {e}")
            results.append(False)
        
        # 测试 has_chinese_subtitle
        try:
            movie_dir = Path(test_dir, "movie")
            movie_dir.mkdir()
            Path(movie_dir, "movie.mkv").touch()
            assert not has_chinese_subtitle(str(movie_dir / "movie.mkv"))
            Path(movie_dir, "movie.zh.srt").touch()
            assert has_chinese_subtitle(str(movie_dir / "movie.mkv"))
            print_success("has_chinese_subtitle 测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"has_chinese_subtitle 测试失败: {e}")
            results.append(False)
        
        # 测试 extract_season_episode
        try:
            assert extract_season_episode("Show.S01E05.mkv") == (1, 5)
            assert extract_season_episode("Show.S02E12.mkv") == (2, 12)
            assert extract_season_episode("Show.mkv") == (None, None)
            print_success("extract_season_episode 测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"extract_season_episode 测试失败: {e}")
            results.append(False)
        
        # 测试 clean_filename
        try:
            assert clean_filename("Movie.2021.1080p.mkv") == "Movie"
            assert clean_filename("TV.Show.S01E05.mkv") == "TV Show"
            print_success("clean_filename 测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"clean_filename 测试失败: {e}")
            results.append(False)
        
        # 测试 normalize_filename
        try:
            assert normalize_filename("Movie.2021.mkv") == "movie"
            assert normalize_filename("TV_Show_S01.mkv") == "tvshow"
            print_success("normalize_filename 测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"normalize_filename 测试失败: {e}")
            results.append(False)
    
    finally:
        shutil.rmtree(test_dir)
    
    return all(results)

def test_config():
    """测试配置"""
    print_header("测试配置")
    
    from config import Config, settings
    
    results = []
    
    try:
        config = Config()
        assert config.MIN_FILE_SIZE == 100 * 1024 * 1024
        assert config.SCAN_INTERVAL == 30
        assert 'subhd' in config.SUBTITLE_SOURCES
        print_success("Config 类测试通过")
        results.append(True)
    except Exception as e:
        print_error(f"Config 类测试失败: {e}")
        results.append(False)
    
    try:
        assert settings.MIN_FILE_SIZE_MB == 100
        assert settings.AUTO_DOWNLOAD == True
        print_success("Settings 对象测试通过")
        results.append(True)
    except Exception as e:
        print_error(f"Settings 对象测试失败: {e}")
        results.append(False)
    
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
            print_success("初始化测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"初始化测试失败: {e}")
            results.append(False)
        
        # 测试统计信息
        try:
            stats = manager.get_stats()
            assert 'totalMovies' in stats
            assert 'totalTVShows' in stats
            print_success("统计信息测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"统计信息测试失败: {e}")
            results.append(False)
        
        # 测试任务管理
        try:
            task_id = manager.add_task('test', {'data': 'test'})
            assert task_id is not None
            task = manager.get_task(task_id)
            assert task is not None
            print_success("任务管理测试通过")
            results.append(True)
        except Exception as e:
            print_error(f"任务管理测试失败: {e}")
            results.append(False)
    
    finally:
        shutil.rmtree(test_dir)
    
    return all(results)

def test_frontend_structure():
    """测试前端结构"""
    print_header("测试前端结构")
    
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
    
    results = []
    for file in required_files:
        file_path = web_dir / file
        if file_path.exists():
            print_success(f"文件存在: {file}")
            results.append(True)
        else:
            print_error(f"文件缺失: {file}")
            results.append(False)
    
    return all(results)

def test_docker_files():
    """测试 Docker 配置文件"""
    print_header("测试 Docker 配置文件")
    
    root_dir = Path(__file__).parent
    
    required_files = [
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        ".env.example",
        "deploy.ps1",
    ]
    
    results = []
    for file in required_files:
        file_path = root_dir / file
        if file_path.exists():
            print_success(f"文件存在: {file}")
            results.append(True)
        else:
            print_error(f"文件缺失: {file}")
            results.append(False)
    
    return all(results)

def start_backend_server():
    """启动后端服务器进行测试"""
    print_header("启动后端服务器测试")
    
    try:
        # 检查依赖
        import fastapi
        import uvicorn
        print_success("FastAPI 和 Uvicorn 已安装")
    except ImportError:
        print_error("FastAPI 或 Uvicorn 未安装")
        print_info("运行: pip install -r requirements.txt")
        return False
    
    # 启动服务器进程
    try:
        print_info("正在启动后端服务器...")
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "api_server:app", "--host", "127.0.0.1", "--port", "8080"],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        # 测试健康检查
        import urllib.request
        try:
            response = urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=5)
            data = json.loads(response.read().decode())
            if data.get("status") == "healthy":
                print_success("后端服务器运行正常")
                print_success("API 地址: http://127.0.0.1:8080")
                print_success("API 文档: http://127.0.0.1:8080/docs")
                return process
            else:
                print_error("健康检查失败")
                process.terminate()
                return False
        except Exception as e:
            print_error(f"无法连接到后端服务器: {e}")
            process.terminate()
            return False
            
    except Exception as e:
        print_error(f"启动服务器失败: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "="*70)
    print("  字幕管理器本地测试")
    print("="*70)
    
    all_results = []
    
    # 运行所有测试
    all_results.append(("Python 环境", test_python_environment()))
    all_results.append(("模块导入", test_imports()))
    all_results.append(("配置测试", test_config()))
    all_results.append(("工具函数", test_utils()))
    all_results.append(("字幕管理器", test_subtitle_manager()))
    all_results.append(("前端结构", test_frontend_structure()))
    all_results.append(("Docker 配置", test_docker_files()))
    
    # 打印总结
    print_header("测试总结")
    
    total = len(all_results)
    passed = sum(1 for _, result in all_results if result)
    failed = total - passed
    
    for name, result in all_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print("\n" + "-"*70)
    print(f"  总计: {total} | 通过: {passed} | 失败: {failed}")
    print("="*70)
    
    if failed == 0:
        print("\n  🎉 所有测试通过！")
        print("\n  你可以选择以下方式运行系统：")
        print("  1. 本地开发模式: python start_server.py")
        print("  2. Docker 模式: .\deploy.ps1 -Start")
        return 0
    else:
        print(f"\n  ⚠️  {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
