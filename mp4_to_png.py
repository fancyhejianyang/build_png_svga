try:
    import cv2
    print("OpenCV imported successfully")
except ImportError as e:
    print(f"Error importing OpenCV: {e}")
    print("Please install opencv-python: pip install opencv-python")
    import sys
    sys.exit(1)

import os
import sys
from pathlib import Path

def extract_frames_from_mp4(mp4_path, output_dir, target_fps=120):
    """
    从MP4视频中按指定帧率提取帧并保存为PNG文件
    
    Args:
        mp4_path (str): MP4文件路径
        output_dir (str): 输出目录路径
        target_fps (int): 目标帧率，默认120fps
    """
    # 打开视频文件
    cap = cv2.VideoCapture(mp4_path)
    
    if not cap.isOpened():
        print(f"错误：无法打开视频文件 {mp4_path}")
        return False
    
    # 获取视频信息
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / original_fps
    
    print(f"视频信息:")
    print(f"  原始帧率: {original_fps:.2f} fps")
    print(f"  总帧数: {total_frames}")
    print(f"  时长: {duration:.2f} 秒")
    print(f"  目标帧率: {target_fps} fps")
    
    # 计算帧间隔
    frame_interval = original_fps / target_fps if original_fps > target_fps else 1
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    print(f"输出目录: {output_dir}")
    print(f"输出目录绝对路径: {os.path.abspath(output_dir)}")
    
    frame_count = 0
    extracted_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 根据帧间隔决定是否提取当前帧
        if frame_count % max(1, int(frame_interval)) == 0:
            # 生成文件名，格式：frame_0001.png
            filename = f"frame_{extracted_count + 1:04d}.png"
            filepath = os.path.join(output_dir, filename)
            
            # 保存帧为PNG
            cv2.imwrite(filepath, frame)
            extracted_count += 1
            
            if extracted_count % 50 == 0:
                print(f"已提取 {extracted_count} 帧...")
        
        frame_count += 1
    
    cap.release()
    
    print(f"提取完成！共提取 {extracted_count} 帧到目录: {output_dir}")
    return True

def process_all_mp4_files(uploads_dir="uploads", assets_dir="assets"):
    """
    处理uploads目录下的所有MP4文件
    
    Args:
        uploads_dir (str): 上传文件目录
        assets_dir (str): 资源输出目录
    """
    uploads_path = Path(uploads_dir)
    assets_path = Path(assets_dir)
    
    if not uploads_path.exists():
        print(f"错误：uploads目录不存在: {uploads_path}")
        return
    
    # 查找所有MP4文件
    mp4_files = list(uploads_path.glob("*.mp4"))
    
    if not mp4_files:
        print("未找到MP4文件")
        return
    
    print(f"找到 {len(mp4_files)} 个MP4文件:")
    for mp4_file in mp4_files:
        print(f"  - {mp4_file.name}")
    
    # 处理每个MP4文件
    for mp4_file in mp4_files:
        print(f"\n正在处理: {mp4_file.name}")
        
        # 创建以视频文件名命名的输出目录
        video_name = mp4_file.stem  # 不包含扩展名的文件名
        output_dir = assets_path / video_name
        
        # 提取帧
        success = extract_frames_from_mp4(str(mp4_file), str(output_dir), target_fps=120)
        
        if success:
            print(f"✓ {mp4_file.name} 处理完成")
        else:
            print(f"✗ {mp4_file.name} 处理失败")

def main():
    """主函数"""
    print("MP4视频帧提取工具")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("用法:")
            print("  python mp4_to_png.py                    # 处理uploads目录下的所有MP4文件")
            print("  python mp4_to_png.py <mp4_file_path>    # 处理指定的MP4文件")
            print("  python mp4_to_png.py --help             # 显示帮助信息")
            return
        
        # 处理指定的MP4文件
        mp4_path = sys.argv[1]
        if not os.path.exists(mp4_path):
            print(f"错误：文件不存在: {mp4_path}")
            return
        
        # 生成输出目录名
        video_name = Path(mp4_path).stem
        output_dir = f"assets/{video_name}"
        
        extract_frames_from_mp4(mp4_path, output_dir, target_fps=120)
    else:
        # 处理uploads目录下的所有MP4文件
        process_all_mp4_files()

if __name__ == "__main__":
    main()
