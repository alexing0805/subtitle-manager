import aiohttp
import hashlib
import struct
from typing import List
from loguru import logger

from . import BaseSubtitleSource, SubtitleResult


class ShooterSource(BaseSubtitleSource):
    """
    射手网字幕源 - 使用文件哈希匹配算法
    射手网通过视频文件的前64KB和后64KB的哈希值来匹配字幕
    """
    
    def __init__(self):
        super().__init__("Shooter")
        self.api_url = "https://www.shooter.cn/api/subapi.php"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        }
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算射手网文件哈希
        取文件前64KB和后64KB的MD5哈希值
        """
        try:
            with open(file_path, 'rb') as f:
                # 获取文件大小
                f.seek(0, 2)
                file_size = f.tell()
                
                # 读取前64KB
                f.seek(0)
                front_data = f.read(64 * 1024)
                
                # 读取后64KB
                if file_size > 64 * 1024:
                    f.seek(-64 * 1024, 2)
                    back_data = f.read(64 * 1024)
                else:
                    back_data = front_data
                
                # 计算哈希
                front_hash = hashlib.md5(front_data).hexdigest()
                back_hash = hashlib.md5(back_data).hexdigest()
                
                return f"{front_hash};{back_hash}"
        except Exception as e:
            logger.error(f"计算文件哈希失败: {e}")
            return None
    
    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """
        搜索字幕 - 射手网需要文件路径来计算哈希
        如果 video_info 中没有 path，则返回空结果
        """
        results = []
        
        video_path = video_info.get('path')
        if not video_path:
            logger.debug("射手网搜索需要视频文件路径")
            return results
        
        try:
            # 计算文件哈希
            file_hash = self._calculate_file_hash(video_path)
            if not file_hash:
                return results
            
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 构建请求参数
                params = {
                    "filehash": file_hash,
                    "pathinfo": video_info.get('filename', ''),
                    "format": "json",
                    "lang": "Chn"  # 中文
                }
                
                logger.info(f"射手网搜索: {video_info.get('name')}, hash={file_hash}")
                
                async with session.post(self.api_url, data=params, timeout=30) as response:
                    if response.status == 200:
                        # 射手网返回的是 JSON 但 Content-Type 可能是 application/octet-stream
                        # 尝试多种编码
                        try:
                            text = await response.text(encoding='utf-8')
                        except:
                            try:
                                text = await response.text(encoding='gbk')
                            except:
                                text = await response.text(encoding='latin-1')

                        try:
                            import json
                            data = json.loads(text)
                        except json.JSONDecodeError as e:
                            logger.warning(f"射手网返回非 JSON 数据: {e}, 内容: {text[:100]}")
                            return results

                        if isinstance(data, list):
                            for item_index, item in enumerate(data):
                                if 'Files' in item:
                                    for file_index, file_info in enumerate(item['Files']):
                                        # 生成唯一ID
                                        subtitle_id = hashlib.md5(
                                            f"{self.name}_{file_hash}_{item_index}_{file_index}_{file_info.get('Ext', '')}".encode()
                                        ).hexdigest()[:12]
                                        result = SubtitleResult(
                                            id=subtitle_id,
                                            source=self.name,
                                            title=file_info.get('FilmName', '未知字幕'),
                                            language="zh-cn",
                                            download_url=file_info.get('Link', ''),
                                            score=0.9,  # 哈希匹配通常很准确
                                            file_format=file_info.get('Ext', 'srt')
                                        )
                                        results.append(result)

                        logger.info(f"射手网返回 {len(results)} 个结果")
                    else:
                        logger.warning(f"射手网搜索失败: {response.status}")
                        
        except Exception as e:
            logger.error(f"射手网搜索异常: {e}")
        
        return results
    
    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool | str:
        """下载字幕"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(subtitle_result.download_url, timeout=30) as response:
                    if response.status == 200:
                        content = await response.read()
                        saved_path = await self._save_download_content(
                            content,
                            save_path,
                            file_url=subtitle_result.download_url,
                            preferred_format=subtitle_result.file_format,
                        )
                        if saved_path:
                            logger.info(f"字幕下载成功: {saved_path}")
                            return saved_path
                        logger.error("字幕保存失败")
                        return False
                    else:
                        logger.error(f"下载失败，状态码: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"下载字幕异常: {e}")
            return False
