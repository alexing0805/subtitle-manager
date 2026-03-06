import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
from loguru import logger
import asyncio
from typing import Callable

from config import settings
from utils import get_video_files


class VideoFileHandler(FileSystemEventHandler):
    """视频文件事件处理器"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.processed_files = set()
    
    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
        
        if self._is_video_file(event.src_path):
            logger.info(f"检测到新文件: {event.src_path}")
            # 等待文件写入完成
            self._wait_for_file_complete(event.src_path)
            self.callback(event.src_path)
    
    def on_moved(self, event):
        """文件移动事件（硬链接创建会触发此事件）"""
        if event.is_directory:
            return
        
        if self._is_video_file(event.dest_path):
            logger.info(f"检测到文件移动/硬链接: {event.dest_path}")
            # 等待文件写入完成
            self._wait_for_file_complete(event.dest_path)
            self.callback(event.dest_path)
    
    def _is_video_file(self, filepath: str) -> bool:
        """检查是否为视频文件"""
        return any(filepath.lower().endswith(ext) for ext in settings.VIDEO_EXTENSIONS)
    
    def _wait_for_file_complete(self, filepath: str, timeout: int = 60):
        """等待文件写入完成"""
        start_time = time.time()
        last_size = -1
        stable_count = 0
        
        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(filepath)
                if current_size == last_size:
                    stable_count += 1
                    if stable_count >= 3:  # 文件大小稳定3次认为写入完成
                        return
                else:
                    stable_count = 0
                    last_size = current_size
            except OSError:
                pass
            time.sleep(1)
        
        logger.warning(f"等待文件写入超时: {filepath}")


class DirectoryWatcher:
    """目录监控器"""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.observers = []
        self.handler = VideoFileHandler(callback)
    
    def start(self):
        """启动监控"""
        for watch_dir in settings.WATCH_DIRS:
            if os.path.exists(watch_dir):
                observer = Observer()
                observer.schedule(self.handler, watch_dir, recursive=True)
                observer.start()
                self.observers.append(observer)
                logger.info(f"开始监控目录: {watch_dir}")
            else:
                logger.warning(f"监控目录不存在，跳过: {watch_dir}")
    
    def stop(self):
        """停止监控"""
        for observer in self.observers:
            observer.stop()
        
        for observer in self.observers:
            observer.join()
        
        logger.info("目录监控已停止")
    
    def scan_existing(self) -> list:
        """扫描现有文件"""
        all_files = []
        for watch_dir in settings.WATCH_DIRS:
            if os.path.exists(watch_dir):
                files = get_video_files(watch_dir)
                all_files.extend(files)
                logger.info(f"目录 {watch_dir} 现有 {len(files)} 个视频文件")
        return all_files


async def watch_directories(callback: Callable[[str], None]):
    """启动目录监控（异步包装）"""
    watcher = DirectoryWatcher(callback)
    watcher.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        watcher.stop()
        raise
