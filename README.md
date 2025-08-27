# PNG 序列转 SVGA 2.0 格式转换器

这个项目可以将一系列按顺序命名的 PNG 图片转换为 SVGA 2.0 格式的动画文件。

## 功能特点

- 支持 SVGA 2.0 标准格式
- 自动识别和排序 PNG 序列帧
- 支持自定义帧率设置
- 使用 zlib 压缩优化文件大小
- 支持不同尺寸图片的自动调整

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python png_to_svga.py
```

这将使用默认设置：
- 输入目录：`assets/`
- 输出文件：`animation.svga`
- 帧率：30 FPS

### 自定义参数

```bash
python png_to_svga.py --input assets --output my_animation.svga --fps 24
```

### 参数说明

- `--input, -i`: PNG 文件所在目录（默认：assets）
- `--output, -o`: 输出的 SVGA 文件名（默认：animation.svga）
- `--fps, -f`: 动画帧率（默认：30）

支持的帧率值：1, 2, 3, 5, 6, 10, 12, 15, 20, 30, 60

## 文件命名规范

PNG 文件应该按以下格式命名：
- `xxx_frame_0001.png`
- `xxx_frame_0002.png`
- `xxx_frame_0003.png`
- ...

或者简单的数字序列：
- `001.png`
- `002.png`
- `003.png`
- ...

## 项目结构

```
├── assets/                 # PNG 序列帧目录
├── png_processor.py        # PNG 图像处理模块
├── svga_encoder.py         # SVGA 格式编码器
├── svga_pb2.py            # ProtoBuf 生成的消息类
├── png_to_svga.py         # 主转换脚本
├── requirements.txt       # 依赖包列表
└── README.md             # 说明文档
```

## SVGA 格式说明

SVGA 2.0 使用 ProtoBuf 定义数据结构，包含：
- 动画参数（尺寸、帧率、总帧数）
- 图像数据（PNG 二进制数据）
- 精灵实体（每帧的显示属性）
- 变换矩阵（位置、缩放、旋转等）

最终文件使用 zlib 压缩以减小文件大小。
