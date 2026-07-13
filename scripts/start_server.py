#!/usr/bin/env python3
"""
字幕管理器启动脚本
同时启动后端 API 和前端开发服务器
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"

def start_backend():
    """启动后端 API 服务器"""
    print("🚀 启动后端 API 服务器...")
    print("   地址: http://localhost:8080")
    print("   API 文档: http://localhost:8080/docs")
    print()
    
    # 使用 uvicorn 启动 FastAPI
    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.api_server:app",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--reload"
    ]
    
    return subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

def start_frontend():
    """启动前端开发服务器"""
    print("🎨 启动前端开发服务器...")
    print("   地址: http://localhost:5173")
    print()
    
    # 检查 node_modules 是否存在
    if not (WEB_DIR / "node_modules").exists():
        print("⚠️  前端依赖未安装，正在安装...")
        subprocess.run(["npm", "install"], cwd=WEB_DIR, check=True)
    
    cmd = ["npm", "run", "dev"]
    
    return subprocess.Popen(
        cmd,
        cwd=WEB_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

def print_output(process, prefix):
    """打印进程输出"""
    try:
        for line in process.stdout:
            print(f"[{prefix}] {line}", end='')
    except:
        pass

def main():
    """主函数"""
    print("="*60)
    print("  字幕管理器启动脚本")
    print("="*60)
    print()
    
    backend_process = None
    frontend_process = None
    
    try:
        # 启动后端
        backend_process = start_backend()
        time.sleep(2)  # 等待后端启动
        
        # 检查后端是否成功启动
        if backend_process.poll() is not None:
            print("❌ 后端启动失败")
            return 1
        
        print("✅ 后端已启动")
        print()
        
        # 启动前端
        try:
            frontend_process = start_frontend()
            time.sleep(3)  # 等待前端启动
            
            if frontend_process.poll() is not None:
                print("⚠️  前端启动失败，但后端仍在运行")
                print("   你可以直接访问 http://localhost:8080 使用 API")
            else:
                print("✅ 前端已启动")
        except Exception as e:
            print(f"⚠️  前端启动失败: {e}")
            print("   后端仍在运行: http://localhost:8080")
        
        print()
        print("="*60)
        print("  服务已启动！")
        print("="*60)
        print()
        print("  📱 Web 界面: http://localhost:5173")
        print("  🔌 API 地址: http://localhost:8080")
        print("  📚 API 文档: http://localhost:8080/docs")
        print()
        print("  按 Ctrl+C 停止服务")
        print()
        
        # 等待进程
        while True:
            time.sleep(1)
            
            # 检查后端是否还在运行
            if backend_process.poll() is not None:
                print("❌ 后端进程已退出")
                break
            
    except KeyboardInterrupt:
        print("\n\n🛑 正在停止服务...")
    finally:
        # 清理进程
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except:
                frontend_process.kill()
        
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except:
                backend_process.kill()
        
        print("✅ 服务已停止")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
