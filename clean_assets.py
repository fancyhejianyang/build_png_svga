import os
import glob
from pathlib import Path

def clean_assets_directory():
    """清理assets目录中的PNG文件，保留文件夹结构"""
    assets_path = Path("assets")
    
    if not assets_path.exists():
        print("assets目录不存在")
        return
    
    # 删除所有PNG文件
    png_files = list(assets_path.glob("*.png"))
    print(f"找到 {len(png_files)} 个PNG文件需要清理")
    
    for png_file in png_files:
        try:
            png_file.unlink()
            print(f"删除: {png_file.name}")
        except Exception as e:
            print(f"删除失败 {png_file.name}: {e}")
    
    print("清理完成")

if __name__ == "__main__":
    clean_assets_directory()
