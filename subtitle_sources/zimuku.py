import aiohttp
import aiofiles
import re
from typing import List
from bs4 import BeautifulSoup
from loguru import logger
import asyncio

from . import BaseSubtitleSource, SubtitleResult


class ZimukuSource(BaseSubtitleSource):
    """字幕库 (Zimuku) 字幕源"""
    
    def __init__(self):
        super().__init__("字幕库")
        self.base_url = "https://zimuku.org"
        self.search_url = f"{self.base_url}/search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://zimuku.org/"
        }
    
    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """搜索字幕"""
        results = []
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 构建搜索关键词
                search_term = video_info['name']
                if video_info.get('year'):
                    search_term += f" {video_info['year']}"
                
                params = {"q": search_term}
                
                async with session.get(self.search_url, params=params, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 解析搜索结果表格
                        results_table = soup.find('table', class_='table')
                        if results_table:
                            rows = results_table.find_all('tr')[1:]  # 跳过表头
                            
                            for row in rows[:5]:  # 只取前5个结果
                                try:
                                    cells = row.find_all('td')
                                    if len(cells) < 3:
                                        continue
                                    
                                    # 获取标题和链接
                                    title_elem = cells[0].find('a')
                                    if not title_elem:
                                        continue
                                    
                                    title = title_elem.get_text(strip=True)
                                    detail_url = self.base_url + title_elem.get('href', '')
                                    
                                    # 获取语言信息
                                    language = "zh"
                                    lang_elem = cells[1] if len(cells) > 1 else None
                                    if lang_elem:
                                        lang_text = lang_elem.get_text(strip=True)
                                        if "简体" in lang_text or "chs" in lang_text.lower():
                                            language = "zh-cn"
                                        elif "繁体" in lang_text or "cht" in lang_text.lower():
                                            language = "zh-tw"
                                    
                                    # 计算匹配度
                                    score = self._calculate_score(title, video_info)
                                    
                                    result = SubtitleResult(
                                        source=self.name,
                                        title=title,
                                        language=language,
                                        download_url=detail_url,
                                        score=score,
                                        file_format="srt"
                                    )
                                    results.append(result)
                                except Exception as e:
                                    logger.debug(f"解析搜索结果项失败: {e}")
                                    continue
                    else:
                        logger.warning(f"字幕库搜索失败: {response.status}")
        except asyncio.TimeoutError:
            logger.warning("字幕库搜索超时")
        except Exception as e:
            logger.error(f"字幕库搜索异常: {e}")
        
        return results
    
    def _calculate_score(self, title: str, video_info: dict) -> float:
        """计算匹配度评分"""
        score = 0.5
        title_lower = title.lower()
        
        # 检查分辨率匹配
        if video_info.get('resolution'):
            if video_info['resolution'].lower() in title_lower:
                score += 0.2
        
        # 检查来源匹配
        if video_info.get('source'):
            if video_info['source'].lower() in title_lower:
                score += 0.2
        
        # 检查压制组
        if video_info.get('group'):
            if video_info['group'].lower() in title_lower:
                score += 0.1
        
        # 检查季和集匹配（如果是剧集）
        if video_info.get('season') and video_info.get('episode'):
            season_ep_pattern = f"s{video_info['season']:02d}e{video_info['episode']:02d}"
            if season_ep_pattern in title_lower:
                score += 0.1
        
        return min(score, 1.0)
    
    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool:
        """下载字幕"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 访问详情页获取下载链接
                async with session.get(subtitle_result.download_url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # 查找下载链接
                        download_div = soup.find('div', class_='download-box')
                        if download_div:
                            download_link = download_div.find('a', href=re.compile(r'/download/'))
                            if download_link:
                                download_path = download_link.get('href')
                                if download_path:
                                    download_url = self.base_url + download_path
                                    
                                    # 下载字幕文件
                                    async with session.get(download_url, timeout=60) as file_response:
                                        if file_response.status == 200:
                                            content = await file_response.read()
                                            
                                            # 处理可能的压缩包
                                            if b'PK' in content[:2]:  # ZIP文件
                                                import zipfile
                                                import io
                                                try:
                                                    with zipfile.ZipFile(io.BytesIO(content)) as zf:
                                                        # 找到字幕文件
                                                        for name in zf.namelist():
                                                            if name.lower().endswith(('.srt', '.ass', '.ssa')):
                                                                with zf.open(name) as subfile:
                                                                    sub_content = subfile.read()
                                                                    async with aiofiles.open(save_path, 'wb') as f:
                                                                        await f.write(sub_content)
                                                                    logger.info(f"字幕下载成功: {save_path}")
                                                                    return True
                                                except Exception as e:
                                                    logger.error(f"解压ZIP失败: {e}")
                                            elif b'Rar!' in content[:4]:  # RAR文件
                                                logger.warning("RAR格式暂不支持自动解压")
                                                return False
                                            else:
                                                # 直接保存
                                                async with aiofiles.open(save_path, 'wb') as f:
                                                    await f.write(content)
                                                logger.info(f"字幕下载成功: {save_path}")
                                                return True
                        else:
                            # 尝试其他方式查找下载链接
                            download_link = soup.find('a', href=re.compile(r'/download/'))
                            if download_link:
                                download_path = download_link.get('href')
                                download_url = self.base_url + download_path if download_path.startswith('/') else download_path
                                
                                async with session.get(download_url, timeout=60) as file_response:
                                    if file_response.status == 200:
                                        content = await file_response.read()
                                        async with aiofiles.open(save_path, 'wb') as f:
                                            await f.write(content)
                                        logger.info(f"字幕下载成功: {save_path}")
                                        return True
                    else:
                        logger.warning(f"获取下载页面失败: {response.status}")
        except asyncio.TimeoutError:
            logger.warning("字幕库下载超时")
        except Exception as e:
            logger.error(f"下载字幕异常: {e}")
        
        return False
