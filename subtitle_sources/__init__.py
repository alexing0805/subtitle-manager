from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SubtitleResult:
    """字幕搜索结果"""
    source: str
    title: str
    language: str
    download_url: str
    score: float  # 匹配度评分 0-1
    file_format: str = "srt"
    

class BaseSubtitleSource(ABC):
    """字幕源基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def search(self, video_info: dict) -> List[SubtitleResult]:
        """搜索字幕"""
        pass
    
    @abstractmethod
    async def download(self, subtitle_result: SubtitleResult, save_path: str) -> bool:
        """下载字幕"""
        pass


from .opensubtitles import OpenSubtitlesSource
from .subhd import SubHDSource
from .zimuku import ZimukuSource


# 可用的字幕源
AVAILABLE_SOURCES = {
    'opensubtitles': OpenSubtitlesSource,
    'subhd': SubHDSource,
    'zimuku': ZimukuSource,
}


def get_source(name: str) -> Optional[BaseSubtitleSource]:
    """获取字幕源实例"""
    source_class = AVAILABLE_SOURCES.get(name.lower())
    if source_class:
        return source_class()
    return None
