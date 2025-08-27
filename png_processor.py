import os
import re
from PIL import Image
import numpy as np
from typing import List, Tuple, Dict

class PNGProcessor:
    """处理 PNG 序列帧的类"""
    
    def __init__(self, assets_dir: str):
        self.assets_dir = assets_dir
        self.frames = []
        self.frame_size = None
        
    def load_png_sequence(self) -> List[Tuple[str, bytes]]:
        """加载 PNG 序列帧，返回 (文件名, 二进制数据) 列表"""
        png_files = []
        
        # 获取所有 PNG 文件
        for filename in os.listdir(self.assets_dir):
            if filename.lower().endswith('.png'):
                png_files.append(filename)
        
        # 按帧序号排序
        png_files.sort(key=self._extract_frame_number)
        
        frames_data = []
        for filename in png_files:
            filepath = os.path.join(self.assets_dir, filename)
            
            # 读取图像获取尺寸信息
            with Image.open(filepath) as img:
                if self.frame_size is None:
                    self.frame_size = img.size
                elif img.size != self.frame_size:
                    # 如果尺寸不一致，调整为统一尺寸
                    img = img.resize(self.frame_size, Image.Resampling.LANCZOS)
            
            # 读取二进制数据
            with open(filepath, 'rb') as f:
                png_data = f.read()
            
            frames_data.append((filename, png_data))
            
        self.frames = frames_data
        return frames_data
    
    def _extract_frame_number(self, filename: str) -> int:
        """从文件名中提取帧序号"""
        # 匹配类似 "xxx_frame_0001.png" 的模式
        match = re.search(r'frame_(\d+)', filename)
        if match:
            return int(match.group(1))
        
        # 如果没有找到 frame_ 模式，尝试提取最后的数字
        match = re.search(r'(\d+)\.png$', filename)
        if match:
            return int(match.group(1))
        
        return 0
    
    def get_frame_count(self) -> int:
        """获取帧数"""
        return len(self.frames)
    
    def get_frame_size(self) -> Tuple[int, int]:
        """获取帧尺寸 (width, height)"""
        return self.frame_size if self.frame_size else (0, 0)
    
    def get_frame_data(self, index: int) -> bytes:
        """获取指定索引的帧数据"""
        if 0 <= index < len(self.frames):
            return self.frames[index][1]
        return b''
    
    def get_frame_key(self, index: int) -> str:
        """获取指定索引的帧键名"""
        if 0 <= index < len(self.frames):
            # 使用简化的键名，去掉文件扩展名
            filename = self.frames[index][0]
            return os.path.splitext(filename)[0]
        return f"frame_{index:04d}"
