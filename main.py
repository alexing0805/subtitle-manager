import os
import sys
import asyncio
import signal
from datetime import datetime
from loguru import logger
import schedule

from config import settings
from subtitle_manager import SubtitleManager
from watcher import DirectoryWatcher, watch_directories

# 配置日志
log_dir = "/app/logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"subtitle_manager_{datetime.now().strftime('%Y%m%d')}.log")

logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
logger.add(log_file, level="DEBUG", rotation="10 MB", retention="7 days", encoding="utf-8")


class SubtitleService:
    """字幕服务主类"""
    
    def __init__(self):
        self.manager = SubtitleManager()
        self.watcher = None
        self.running = False
        self.scan_task = None
        self.watch_task = None
    
    async def start(self):
        """启动服务"""
        logger.info("=" * 60)
        logger.info("字幕管理服务启动")
        logger.info("=" * 60)
        logger.info(f"监控目录: {settings.WATCH_DIRS}")
        logger.info(f"扫描间隔: {settings.SCAN_INTERVAL} 分钟")
        logger.info(f"字幕源: {settings.SUBTITLE_SOURCES}")
        logger.info(f"自动下载: {settings.AUTO_DOWNLOAD}")
        logger.info("=" * 60)
        
        self.running = True
        
        # 首次扫描现有文件
        await self.manager.scan_and_process()
        
        # 设置定时扫描
        if settings.SCAN_INTERVAL > 0:
            schedule.every(settings.SCAN_INTERVAL).minutes.do(self._scheduled_scan)
            logger.info(f"已设置定时扫描: 每 {settings.SCAN_INTERVAL} 分钟")
        
        # 启动目录监控
        self.watcher = DirectoryWatcher(self._on_new_file)
        self.watcher.start()
        
        # 启动调度器
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(1)
    
    def _scheduled_scan(self):
        """定时扫描任务"""
        logger.info("执行定时扫描...")
        asyncio.create_task(self.manager.scan_and_process())
    
    def _on_new_file(self, filepath: str):
        """新文件回调"""
        logger.info(f"监控到新文件，开始处理: {filepath}")
        asyncio.create_task(self.manager.process_single_file(filepath))
    
    def stop(self):
        """停止服务"""
        logger.info("正在停止服务...")
        self.running = False
        if self.watcher:
            self.watcher.stop()
        logger.info("服务已停止")


async def main():
    """主函数"""
    service = SubtitleService()
    
    # 设置信号处理
    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，正在关闭...")
        service.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except Exception as e:
        logger.error(f"服务异常: {e}")
        raise
    finally:
        service.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
