import os
import re
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger
import chardet

from config import settings


def get_video_files(directory: str) -> List[str]:
    """获取目录下所有视频文件"""
    video_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in settings.VIDEO_EXTENSIONS):
                filepath = os.path.join(root, file)
                # 检查文件大小
                try:
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    if size_mb >= settings.MIN_FILE_SIZE_MB:
                        video_files.append(filepath)
                except OSError:
                    continue
    return video_files


def get_subtitle_files(video_path: str) -> List[str]:
    """获取视频文件对应的所有字幕文件"""
    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    subtitle_files = []
    for file in os.listdir(video_dir):
        if any(file.lower().endswith(ext) for ext in settings.SUBTITLE_EXTENSIONS):
            # 检查文件名是否匹配
            file_name = os.path.splitext(file)[0]
            if file_name.startswith(video_name) or video_name.startswith(file_name):
                subtitle_files.append(os.path.join(video_dir, file))
    
    return subtitle_files


def has_chinese_subtitle(video_path: str) -> bool:
    """检查视频是否已有中文字幕"""
    subtitle_files = get_subtitle_files(video_path)
    
    for sub_file in subtitle_files:
        file_name = os.path.basename(sub_file).lower()
        
        # 检查文件名中是否包含中文标识
        for lang_code in settings.CHINESE_LANG_CODES:
            if lang_code.lower() in file_name:
                return True
        
        # 检查字幕文件内容
        try:
            if is_chinese_subtitle_content(sub_file):
                return True
        except Exception as e:
            logger.warning(f"检查字幕文件内容失败 {sub_file}: {e}")
    
    return False


def is_chinese_subtitle_content(subtitle_path: str) -> bool:
    """检查字幕文件内容是否包含中文"""
    try:
        # 检测文件编码
        with open(subtitle_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # 读取内容
        with open(subtitle_path, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        
        # 检查中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
        return len(chinese_chars) > 10  # 至少有10个中文字符
    except Exception as e:
        logger.error(f"读取字幕文件失败 {subtitle_path}: {e}")
        return False


def extract_video_info(video_path: str) -> dict:
    """从视频文件名提取信息"""
    filename = os.path.basename(video_path)
    name_without_ext = os.path.splitext(filename)[0]
    
    info = {
        'path': video_path,
        'filename': filename,
        'name': name_without_ext,
        'dir': os.path.dirname(video_path),
        'year': None,
        'season': None,
        'episode': None,
        'resolution': None,
        'source': None,
        'group': None
    }
    
    # 提取年份 (1900-2099)
    year_match = re.search(r'(19|20)\d{2}', name_without_ext)
    if year_match:
        info['year'] = year_match.group()
    
    # 提取季和集 (S01E01, S1E1, Season 1 Episode 1 等格式)
    season_ep_match = re.search(r'[Ss](\d{1,2})[Ee](\d{1,2})', name_without_ext)
    if season_ep_match:
        info['season'] = int(season_ep_match.group(1))
        info['episode'] = int(season_ep_match.group(2))
    
    # 提取分辨率
    res_match = re.search(r'(1080p|720p|2160p|4K|8K)', name_without_ext, re.IGNORECASE)
    if res_match:
        info['resolution'] = res_match.group(1).lower()
    
    # 提取来源 (WEB-DL, BluRay, HDRip 等)
    source_match = re.search(r'(WEB-DL|BluRay|BRRip|HDRip|DVDRip|HDTV|WEBRip)', name_without_ext, re.IGNORECASE)
    if source_match:
        info['source'] = source_match.group(1)
    
    # 提取压制组
    group_match = re.search(r'-([A-Za-z0-9]+)$', name_without_ext)
    if group_match:
        info['group'] = group_match.group(1)
    
    return info


def calculate_file_hash(filepath: str, algorithm: str = 'md5') -> str:
    """计算文件哈希值"""
    hash_obj = hashlib.new(algorithm)
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"计算文件哈希失败 {filepath}: {e}")
        return ""


def get_subtitle_save_path(video_path: str, lang_code: str = "zh") -> str:
    """获取字幕保存路径"""
    video_dir = os.path.dirname(video_path)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    return os.path.join(video_dir, f"{video_name}.{lang_code}.srt")


def clean_filename(filename: str) -> str:
    """清理文件名，移除特殊字符"""
    # 移除或替换非法字符
    cleaned = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除多余空格
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def is_movie_file(video_path: str) -> bool:
    """判断是否为电影文件（非剧集）"""
    info = extract_video_info(video_path)
    return info['season'] is None and info['episode'] is None


def is_tv_episode(video_path: str) -> bool:
    """判断是否为剧集文件"""
    info = extract_video_info(video_path)
    return info['season'] is not None and info['episode'] is not None
