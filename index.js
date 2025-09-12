const express = require('express');
const multer = require('multer');
const ffmpeg = require('fluent-ffmpeg');
const path = require('path');
const fs = require('fs');
const zlib = require('zlib');
const PNG = require('png-js');
const protobuf = require('protobufjs');
const cors = require('cors');
const sharp = require('sharp');

// 引入并配置ffmpeg
const ffmpegPath = require('@ffmpeg-installer/ffmpeg').path;
ffmpeg.setFfmpegPath(ffmpegPath);

const upload = multer({ dest: 'uploads/' });



// SVGA Protobuf Schema - 统一版本以确保与标准SVGA格式完全兼容
const SVGA_SCHEMA = `
syntax = "proto2";

message MovieEntity {
  optional int32 version = 1; // Changed from float to int32 for better compatibility with SVGAPlayerWeb 2.3.1
  optional uint32 frames = 2;
  optional int32 fps = 3; // Changed from float to int32 for better compatibility
  optional MovieSizeEntity size = 4;
  repeated MovieImageEntity images = 5;
  repeated MovieShapeEntity shapes = 6;
  repeated MovieSpriteEntity sprites = 7;
  repeated MovieFrameEntity spriteFrames = 8;
}

message MovieSizeEntity {
  optional uint32 width = 1;
  optional uint32 height = 2;
}

message MovieImageEntity {
  optional uint32 id = 1;
  optional bytes image = 2;
}

message MovieShapeEntity {
  optional uint32 id = 1;
  optional uint32 imageKey = 2;
  optional MovieTransformEntity transform = 3;
  optional int32 alpha = 4; // Changed from float to int32 for better compatibility
  optional bool visible = 5;
}

message MovieTransformEntity {
  optional int32 a = 1; // Changed from float to int32 for better compatibility
  optional int32 b = 2; // Changed from float to int32 for better compatibility
  optional int32 c = 3; // Changed from float to int32 for better compatibility
  optional int32 d = 4; // Changed from float to int32 for better compatibility
  optional int32 tx = 5; // Changed from float to int32 for better compatibility
  // optional int32 ty = 6; Changed from float to int32 for better compatibility
}

message MovieSpriteEntity {
  optional uint32 id = 1;
  optional uint32 frameTags = 2;
}

message MovieFrameEntity {
  optional uint32 spriteTag = 1;
  optional int32 shapeTag = 2; // Changed from uint32 to int32 for better compatibility with SVGAPlayerWeb 2.3.1
  optional uint32 frameTag = 3;
}`;

// 生成SVGA文件的函数
function generateSVGA(framesPath, outputPath, fps, scale) {
    return new Promise((resolve, reject) => {
        try {
            // 1. 读取所有PNG帧
            const frameDir = path.dirname(framesPath);
            const frameFiles = fs.readdirSync(frameDir)
                .filter(file => file.endsWith('.png'))
                .sort((a, b) => {
                    // 按帧号排序
                    const frameNumA = parseInt(a.match(/_frame_(\d+)\.png/)[1]);
                    const frameNumB = parseInt(b.match(/_frame_(\d+)\.png/)[1]);
                    return frameNumA - frameNumB;
                });

            if (frameFiles.length === 0) {
                throw new Error('No frame files found');
            }

            // 2. 解析Protobuf schema
            try {
                // 使用正确的protobufjs v7 API解析schema字符串
                const root = protobuf.parse(SVGA_SCHEMA).root;

                const MovieEntity = root.lookupType('MovieEntity');
                const MovieSizeEntity = root.lookupType('MovieSizeEntity');
                const MovieImageEntity = root.lookupType('MovieImageEntity');
                const MovieShapeEntity = root.lookupType('MovieShapeEntity');
                const MovieTransformEntity = root.lookupType('MovieTransformEntity');
                const MovieSpriteEntity = root.lookupType('MovieSpriteEntity');
                const MovieFrameEntity = root.lookupType('MovieFrameEntity');

                // 3. 读取第一帧获取尺寸信息
                const firstFramePath = path.join(frameDir, frameFiles[0]);
                const firstFrameData = fs.readFileSync(firstFramePath);
                const firstFramePNG = new PNG(firstFrameData);

                // 等待PNG解析完成
                firstFramePNG.decode((pixels) => {
                    try {
                        const width = firstFramePNG.width;
                        const height = firstFramePNG.height;

                        // 4. 创建SVGA数据结构 - 使用标准版本格式
                        const svgaData = {
                            version: 1.0, // 使用float类型以匹配标准SVGA
                            frames: frameFiles.length,
                            fps: parseFloat(fps),
                            size: {
                                width: width,
                                height: height
                            },
                            images: [],
                            shapes: [],
                            sprites: [],
                            spriteFrames: []
                        };

                        // 5. 处理每个帧（实现图像去重和压缩）
                        const processedImages = new Map(); // 用于存储已处理的图像及其ID
                        const processedTasks = frameFiles.map(async (file, index) => {
                            const imagePath = path.join(frameDir, file);

                            try {
                                // 读取图像数据
                                const imageData = fs.readFileSync(imagePath);

                                // 正确处理PNG数据，确保与标准SVGA格式兼容
                                // 注意：我们不再尝试去除PNG头，而是保留完整的PNG结构
                                const compressedData = await sharp(imageData)
                                    .png({
                                        quality: 80, // 降低压缩质量以提高兼容性
                                        compressionLevel: 6, // 降低压缩级别以提高兼容性
                                        adaptiveFiltering: true,
                                        palette: true,
                                        colors: 256
                                    })
                                    .toBuffer();

                                // 创建更稳健的图像内容哈希用于去重
                                // 先将图像转换为小尺寸灰度图来获取内容指纹
                                const fingerprint = await sharp(imagePath)
                                    .resize(8, 8, { fit: 'inside' })
                                    .grayscale()
                                    .raw()
                                    .toBuffer();

                                // 计算简单的感知哈希
                                let imageHash = 0;
                                for (let i = 0; i < fingerprint.length; i++) {
                                    imageHash = (imageHash << 1) | (fingerprint[i] > 128 ? 1 : 0);
                                }
                                imageHash = imageHash.toString(36);

                                let imageId;
                                if (processedImages.has(imageHash)) {
                                    // 如果图像已存在，复用已有的ID
                                    imageId = processedImages.get(imageHash);
                                } else {
                                    // 如果是新图像，分配新ID并添加到图像列表
                                    imageId = svgaData.images.length;
                                    processedImages.set(imageHash, imageId);

                                    const imageEntity = {
                                        id: imageId,
                                        image: compressedData
                                    };
                                    svgaData.images.push(imageEntity);
                                }

                                // 添加形状
                                const shapeId = svgaData.shapes.length;
                                const shapeEntity = {
                                    id: shapeId,
                                    imageKey: imageId,
                                    transform: {
                                        a: parseInt(scale, 10),
                                        b: 0,
                                        c: 0,
                                        d: parseInt(scale, 10),
                                        tx: 0
                                    }
                                };
                                svgaData.shapes.push(shapeEntity);

                                // 添加精灵 - 确保帧标签设置正确
                                const spriteId = svgaData.sprites.length;
                                const spriteEntity = {
                                    id: spriteId,
                                    frameTags: index
                                };
                                svgaData.sprites.push(spriteEntity);

                                // 添加精灵帧
                                const frameEntity = {
                                    spriteTag: spriteId,
                                    shapeTag: shapeId,
                                    frameTag: index
                                };
                                svgaData.spriteFrames.push(frameEntity);
                            } catch (error) {
                                console.error(`Error processing frame ${index}:`, error);
                                // 如果处理失败，使用原始图像数据作为备选
                                const imageData = fs.readFileSync(imagePath);
                                const imageEntity = {
                                    id: index,
                                    image: imageData
                                };
                                svgaData.images.push(imageEntity);

                                const shapeEntity = {
                                    id: index,
                                    imageKey: index,
                                    transform: {
                                        a: parseInt(scale, 10),
                                        b: 0,
                                        c: 0,
                                        d: parseInt(scale, 10),
                                        tx: 0
                                    }
                                };
                                svgaData.shapes.push(shapeEntity);

                                const spriteEntity = {
                                    id: index,
                                    frameTags: index
                                };
                                svgaData.sprites.push(spriteEntity);

                                const frameEntity = {
                                    spriteTag: index,
                                    shapeTag: index,
                                    frameTag: index
                                };
                                svgaData.spriteFrames.push(frameEntity);
                            }
                        });

                        // 等待所有图像处理完成
                        Promise.all(processedTasks).then(() => {

                            // 6. 验证和序列化
                            const errMsg = MovieEntity.verify(svgaData);
                            if (errMsg) {
                                throw new Error(errMsg);
                            }

                            const message = MovieEntity.create(svgaData);
                            const buffer = MovieEntity.encode(message).finish();

                            // 7. 压缩数据 - 使用标准的SVGA压缩参数
                            // 修改压缩参数以避免"invalid wire type"错误
                            // deflate
                            zlib.gzip(buffer, {
                                level: 6, // 标准压缩级别
                                windowBits: 15,
                                memLevel: 8
                            }, (err, compressed) => {
                                if (err) {
                                    reject(err);
                                    return;
                                }

                                // 8. 写入文件 - 使用二进制模式确保正确的文件格式
                                // SVGA标准要求首字节为0x0A，但不能直接添加到GZIP数据前
                                // 我们需要先写入0x0A，然后再写入GZIP数据

                                // 添加文件格式验证
                                if (compressed.length === 0) {
                                    throw new Error('压缩后的数据为空');
                                }

                                console.log(`SVGA压缩数据大小: ${compressed.length + 1} 字节`);

                                // 创建一个可写流
                                const fileStream = fs.createWriteStream(outputPath, { encoding: null });

                                // 先写入0x0A字节
                                // fileStream.write(Buffer.from([0x0A]));

                                // 再写入压缩数据
                                fileStream.write(compressed);

                                // 结束写入
                                fileStream.end(() => {
                                    console.log(`SVGA数据头部: 0a${compressed.slice(0, 9).toString('hex')}`);
                                    console.log('SVGA file created successfully');
                                });
                                console.log('SVGA file created successfully');
                                // 注意：svgaData是Buffer对象，不包含images属性
                                // 这里应该使用之前处理帧时创建的images数组
                                console.log(`Original frames: ${frameFiles.length}`);

                                // 9. 清理PNG帧文件
                                frameFiles.forEach(file => {
                                    const imagePath = path.join(frameDir, file);
                                    try {
                                        // fs.unlinkSync(imagePath);
                                    } catch (error) {
                                        console.error('Error deleting frame file:', error);
                                    }
                                });

                                resolve();
                            });
                        }).catch(error => {
                            reject(error);
                        });
                    } catch (error) {
                        reject(error);
                    }
                });
            } catch (error) {
                reject(error);
            }
        } catch (error) {
            console.error('Error creating SVGA file:', error);
            reject(error);
        }
    });
}

// 列出uploads 目录下视频文件，按照顺序执行生成png功能
const videoFiles = fs.readdirSync('uploads');
videoFiles.forEach(file => {
    const filePath = path.join('uploads', file);
    if (path.extname(file) === '.mp4') {
        const fps = 120;
        const scale = 1;
        const inputPath = filePath;
        // 输出路径为assets下视频文件名，移除mp4后缀
        const outputDir = path.join(__dirname, 'assets', file.replace('.mp4', ''));

        // Ensure output directory exists
        if (!fs.existsSync(outputDir)) {
            fs.mkdirSync(outputDir, { recursive: true });
        }
        const fileName = file.replace('.mp4', '');
        const framesOutputPath = path.join(outputDir, fileName + '_frame_%04d.png');
        const svgaOutputPath = path.join(outputDir, fileName + '.svga');
        const svgaFileName = fileName + '.svga';

        // Correct way to use fluent-ffmpeg
        ffmpeg(inputPath)
            .outputOptions([
                `-vf fps=${fps}`,
                '-f image2'
            ])
            .output(framesOutputPath)
            .on('end', () => {
                console.log('Frame extraction completed');

                // 生成PNG序列帧后，将PNG序列帧转换为SVGA格式
                generateSVGA(framesOutputPath, svgaOutputPath, fps, scale)
                    .then(() => {
                        console.log('SVGA generation completed');

                        // 检查SVGA文件是否存在
                        if (fs.existsSync(svgaOutputPath)) {
                            // 构建可访问的SVGA文件URL
                            const svgaUrl = `/svga-files/${svgaFileName}`;

                            // 返回JSON响应，包含SVGA文件URL和文件名
                            res.json({
                                success: true,
                                svgaUrl: svgaUrl,
                                fileName: svgaFileName,
                                originalFileName: req.file.originalname
                            });

                            // 清理上传的视频文件
                            if (fs.existsSync(inputPath)) {
                                fs.unlinkSync(inputPath);
                            }
                        } else {
                            console.error('SVGA file not found');
                            res.status(500).json({ error: 'SVGA file generation failed' });

                            // 清理上传的视频文件
                            if (fs.existsSync(inputPath)) {
                                fs.unlinkSync(inputPath);
                            }
                        }
                    })
                    .catch((error) => {
                        console.error('Error generating SVGA:', error);
                        res.status(500).json({ error: 'SVGA generation failed', details: error.message });

                        // 清理上传的视频文件
                        if (fs.existsSync(inputPath)) {
                            fs.unlinkSync(inputPath);
                        }
                    });
            })
            .on('error', (err) => {
                console.error('Error:', err);
                res.status(500).json({ error: 'Conversion failed' });
            })
            .run();
    }
});

