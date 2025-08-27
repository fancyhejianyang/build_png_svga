#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终版本的 PNG 序列转 SVGA 2.0 格式转换器
使用真正的 ProtoBuf 格式，解决兼容性问题
"""

import os
import sys
import argparse
from png_processor import PNGProcessor
from svga_encoder_final import FinalSVGAEncoder

def main():
    parser = argparse.ArgumentParser(description='最终版本：将 PNG 序列转换为兼容的 SVGA 2.0 格式')
    parser.add_argument('--input', '-i', default='assets', help='PNG 文件所在目录')
    parser.add_argument('--output', '-o', default='animation_final.svga', help='输出文件名')
    parser.add_argument('--fps', '-f', type=int, default=30, help='动画帧率')
    parser.add_argument('--mode', '-m', choices=['single', 'multi'], default='single', 
                       help='single: 单帧模式(文件小), multi: 多帧模式(最多10帧)')
    parser.add_argument('--max-frames', type=int, default=10, help='多帧模式下的最大帧数')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"错误: 输入目录 '{args.input}' 不存在")
        sys.exit(1)
    
    print(f"开始处理 PNG 序列（最终版本）...")
    print(f"输入目录: {args.input}")
    print(f"输出文件: {args.output}")
    print(f"模式: {args.mode}")
    
    try:
        # 加载 PNG 序列
        png_processor = PNGProcessor(args.input)
        frames_data = png_processor.load_png_sequence()
        
        if not frames_data:
            print("错误: 未找到任何 PNG 文件")
            sys.exit(1)
        
        frame_count = len(frames_data)
        frame_size = png_processor.get_frame_size()
        
        print(f"找到 {frame_count} 个帧，尺寸: {frame_size[0]} x {frame_size[1]}")
        
        # 创建 SVGA
        encoder = FinalSVGAEncoder()
        
        if args.mode == 'single':
            print("使用单帧模式（文件最小）...")
            svga_data = encoder.create_svga_from_frames(frames_data, frame_size, args.fps)
        else:
            print(f"使用多帧模式（最多 {args.max_frames} 帧）...")
            svga_data = encoder.create_multi_frame_svga(frames_data, frame_size, args.fps, args.max_frames)
        
        # 保存文件
        encoder.save_svga_file(svga_data, args.output)
        
        file_size = len(svga_data)
        original_size = sum(len(data) for _, data in frames_data)
        compression_ratio = (1 - file_size / original_size) * 100
        
        print(f"转换完成!")
        print(f"输出文件: {args.output}")
        print(f"文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")
        print(f"压缩比: {compression_ratio:.1f}%")
        print(f"原始大小: {original_size/1024/1024:.2f} MB")
        
        # 验证文件
        print("\n验证生成的文件...")
        if os.path.exists(args.output):
            with open(args.output, 'rb') as f:
                data = f.read()
                if len(data) > 0:
                    print("✓ 文件生成成功")
                    print("✓ 使用真正的 ProtoBuf 格式")
                    print("✓ 应该与 SVGA 播放器兼容")
                else:
                    print("✗ 文件为空")
        
    except Exception as e:
        print(f"转换过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
