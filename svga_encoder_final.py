import zlib
from typing import Dict, List, Tuple
import svga_pb2

class FinalSVGAEncoder:
    """使用真正的 ProtoBuf 的 SVGA 编码器"""
    
    def __init__(self):
        pass
        
    def create_svga_from_frames(self, 
                               frames_data: List[Tuple[str, bytes]], 
                               frame_size: Tuple[int, int],
                               fps: int = 30) -> bytes:
        """
        创建真正兼容的 SVGA 文件
        """
        width, height = frame_size
        frame_count = len(frames_data)
        
        # 创建 MovieEntity
        movie = svga_pb2.MovieEntity()
        movie.version = "2.0.0"
        
        # 设置参数
        movie.params.viewBoxWidth = float(width)
        movie.params.viewBoxHeight = float(height)
        movie.params.fps = self._validate_fps(fps)
        movie.params.frames = frame_count  # 使用实际选中的帧数
        
        # 只添加第一帧图像以减小文件大小
        first_key, first_data = frames_data[0]
        movie.images[first_key] = first_data
        
        # 创建单个精灵，所有帧都使用同一图像
        sprite = movie.sprites.add()
        sprite.imageKey = first_key
        
        # 为每一帧创建 FrameEntity
        for i in range(frame_count):
            frame = sprite.frames.add()
            frame.alpha = 1.0
            
            # 设置布局
            frame.layout.x = 0.0
            frame.layout.y = 0.0
            frame.layout.width = float(width)
            frame.layout.height = float(height)
            
            # 设置变换矩阵
            frame.transform.a = 1.0
            frame.transform.b = 0.0
            frame.transform.c = 0.0
            frame.transform.d = 1.0
            frame.transform.tx = 0.0
            frame.transform.ty = 0.0
        
        # 序列化为二进制数据
        binary_data = movie.SerializeToString()
        
        # 使用 zlib 压缩
        compressed_data = zlib.compress(binary_data)
        
        return compressed_data
    
    def create_multi_frame_svga(self, 
                               frames_data: List[Tuple[str, bytes]], 
                               frame_size: Tuple[int, int],
                               fps: int = 30,
                               max_frames: int = 10) -> bytes:
        """
        创建多帧 SVGA（限制帧数以控制文件大小）
        """
        # 使用原始图像尺寸作为 viewBox，而不是压缩后的尺寸
        from PIL import Image
        import io
        
        # 获取第一张图片的原始尺寸
        first_image_data = frames_data[0][1]
        with Image.open(io.BytesIO(first_image_data)) as img:
            original_width, original_height = img.size
        
        width, height = original_width, original_height
        
        # 选择关键帧 - 确保包含最后一帧
        total_frames = len(frames_data)
        if total_frames > max_frames:
            # 使用更均匀的分布，确保包含最后一帧
            indices = []
            for i in range(max_frames - 1):
                idx = int(i * (total_frames - 1) / (max_frames - 1))
                indices.append(idx)
            indices.append(total_frames - 1)  # 确保包含最后一帧
            selected_frames = [frames_data[i] for i in indices]
        else:
            selected_frames = frames_data
        
        frame_count = len(selected_frames)
        
        # 创建 MovieEntity
        movie = svga_pb2.MovieEntity()
        movie.version = "2.0.0"
        
        # 设置参数
        movie.params.viewBoxWidth = float(width)
        movie.params.viewBoxHeight = float(height)
        movie.params.fps = self._validate_fps(fps)
        movie.params.frames = frame_count  # 使用实际选中的帧数
        
        # 添加所有选中的图像
        for frame_key, frame_data in selected_frames:
            # 压缩图像数据
            compressed_image = self._compress_image_data(frame_data)
            movie.images[frame_key] = compressed_image
        
        # 为每个图像创建独立的精灵
        for idx, (frame_key, _) in enumerate(selected_frames):
            sprite = movie.sprites.add()
            sprite.imageKey = frame_key
            
            # 为每一帧创建 FrameEntity
            for i in range(frame_count):
                frame = sprite.frames.add()
                
                if i == idx:
                    # 在对应帧显示此精灵
                    frame.alpha = 1.0
                    frame.layout.x = 0.0
                    frame.layout.y = 0.0
                    frame.layout.width = float(width)
                    frame.layout.height = float(height)
                    
                    frame.transform.a = 1.0
                    frame.transform.b = 0.0
                    frame.transform.c = 0.0
                    frame.transform.d = 1.0
                    frame.transform.tx = 0.0
                    frame.transform.ty = 0.0
                else:
                    # 其他帧隐藏此精灵
                    frame.alpha = 0.0
                    frame.layout.x = 0.0
                    frame.layout.y = 0.0
                    frame.layout.width = float(width)
                    frame.layout.height = float(height)
                    
                    frame.transform.a = 1.0
                    frame.transform.b = 0.0
                    frame.transform.c = 0.0
                    frame.transform.d = 1.0
                    frame.transform.tx = 0.0
                    frame.transform.ty = 0.0
        
        # 序列化为二进制数据
        binary_data = movie.SerializeToString()
        
        # 使用 zlib 压缩
        compressed_data = zlib.compress(binary_data)
        
        return compressed_data
    
    def _compress_image_data(self, image_data: bytes) -> bytes:
        """压缩图像数据，保持 PNG 格式"""
        from PIL import Image
        import io
        
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # 记录原始尺寸
                original_width, original_height = img.size
                
                # 适度压缩以保持质量和性能平衡
                max_size = 1080  # 提高到1080p以保持更好的显示效果
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # 确保图像有有效的尺寸
                if img.width == 0 or img.height == 0:
                    # 如果尺寸无效，使用原始数据
                    return image_data
                
                # 保持 PNG 格式，但优化压缩
                output = io.BytesIO()
                
                # 优化保存参数以减少内存使用
                save_kwargs = {
                    'format': 'PNG',
                    'optimize': True,
                    'compress_level': 6  # 降低压缩级别以减少处理时间
                }
                
                # 如果是 RGBA 模式，保持透明度
                if img.mode in ('RGBA', 'LA'):
                    img.save(output, **save_kwargs)
                else:
                    # 转换为 RGB 并保存为 PNG
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(output, **save_kwargs)
                
                compressed_data = output.getvalue()
                
                # 验证压缩后的图像
                try:
                    with Image.open(io.BytesIO(compressed_data)) as test_img:
                        if test_img.width == 0 or test_img.height == 0:
                            # 如果压缩后尺寸无效，返回原始数据
                            return image_data
                except:
                    # 如果压缩后的图像无法打开，返回原始数据
                    return image_data
                
                return compressed_data
                
        except Exception as e:
            # 如果处理失败，返回原始数据
            print(f"图像压缩失败: {e}")
            return image_data
    
    def _validate_fps(self, fps: int) -> int:
        """验证并调整 FPS 值到合法范围"""
        valid_fps = [1, 2, 3, 5, 6, 10, 12, 15, 20, 30, 60]
        closest_fps = min(valid_fps, key=lambda x: abs(x - fps))
        return closest_fps
    
    def save_svga_file(self, svga_data: bytes, output_path: str):
        """保存 SVGA 文件到磁盘"""
        with open(output_path, 'wb') as f:
            f.write(svga_data)
