# 快速开始指南

## 环境准备

### 1. 系统要求
- **操作系统**: Linux (Ubuntu 18.04+) / Windows 10+ / macOS
- **Python**: 3.8 或更高版本
- **GPU** (推荐): NVIDIA GPU with CUDA 10.2+
- **内存**: 至少 8GB RAM
- **硬盘**: 至少 20GB 可用空间

### 2. 安装依赖

#### 2.1 创建虚拟环境
```bash
# 使用conda
conda create -n vigilens python=3.8
conda activate vigilens

# 或使用venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows
```

#### 2.2 安装PaddlePaddle
```bash
# GPU版本
pip install paddlepaddle-gpu==2.4.0 -i https://mirror.baidu.com/pypi/simple

# CPU版本
pip install paddlepaddle==2.4.0 -i https://mirror.baidu.com/pypi/simple
```

#### 2.3 安装项目依赖
```bash
pip install -r requirements.txt
```

#### 2.4 安装PaddleVideo
```bash
cd PaddleVideo-develop
pip install -e .
cd ..
```

## 模型准备

### 下载预训练模型
```bash
# 创建模型目录
mkdir -p models/VideoSwin

# 下载模型文件（示例）
# 将 VideoSwin.json 和 VideoSwin.pdiparams 放入 models/VideoSwin/
```

模型文件结构：
```
models/
└── VideoSwin/
    ├── VideoSwin.json          # 模型结构文件
    └── VideoSwin.pdiparams     # 模型参数文件
```

## 使用方式

### 方式一：命令行推理

```bash
cd src/inference
python run_local.py --video_path /path/to/your/video.mp4
```

参数说明：
- `--video_path`: 视频文件路径
- `--model_file`: 模型文件路径（可选）
- `--params_file`: 参数文件路径（可选）
- `--config_file`: 配置文件路径（可选）

### 方式二：启动Web界面

```bash
cd src/inference
python infer.py
```

然后在浏览器中打开显示的URL（通常是 http://127.0.0.1:7860）

界面功能：
1. 上传视频文件
2. 点击"分析"按钮
3. 查看检测结果和置信度

### 方式三：启动API服务

```bash
cd src/inference
python api.py
```

服务会在 `http://0.0.0.0:5000` 启动

#### API调用示例

使用curl：
```bash
curl -X POST http://localhost:5000/predict \
  -F "video=@/path/to/video.mp4"
```

使用Python：
```python
import requests

url = "http://localhost:5000/predict"
files = {'video': open('video.mp4', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

返回格式：
```json
{
  "success": true,
  "prediction": "violence",
  "confidence": 0.85,
  "message": "检测完成"
}
```

## 配置说明

### 修改配置文件

在 `configs/` 目录下创建或修改配置文件：

```yaml
# violence_detection.yaml
model:
  name: VideoSwin
  num_classes: 2
  
inference:
  batch_size: 1
  num_seg: 1
  seg_len: 32
  
preprocessing:
  short_size: 256
  target_size: 224
  mean: [0.485, 0.456, 0.406]
  std: [0.229, 0.224, 0.225]
```

## 测试数据

### 准备测试视频

```bash
# 将测试视频放入data目录
data/
├── videos/
│   ├── test_video_1.mp4
│   ├── test_video_2.mp4
│   └── ...
```

### 批量测试

```python
import os
from src.inference.infer import predict_video

video_dir = "data/videos/"
for video_file in os.listdir(video_dir):
    video_path = os.path.join(video_dir, video_file)
    result = predict_video(video_path)
    print(f"{video_file}: {result}")
```

## 常见问题

### 1. 导入错误
```
ModuleNotFoundError: No module named 'paddlevideo'
```
**解决**: 确保已安装PaddleVideo
```bash
cd PaddleVideo-develop
pip install -e .
```

### 2. CUDA错误
```
CUDA out of memory
```
**解决**: 减小batch_size或使用CPU模式

### 3. 视频解码失败
```
Failed to decode video
```
**解决**: 
- 确保安装了ffmpeg: `apt install ffmpeg` (Linux) 或 `brew install ffmpeg` (macOS)
- 检查视频格式是否支持

### 4. 模型文件缺失
```
Model file not found
```
**解决**: 检查模型文件路径，确保文件存在

## 性能优化建议

### 1. GPU加速
```bash
# 检查GPU是否可用
python -c "import paddle; print(paddle.device.get_device())"
```

### 2. 使用TensorRT
```python
# 在推理时启用TensorRT
config.enable_tensorrt_engine(
    workspace_size=1 << 30,
    max_batch_size=1,
    min_subgraph_size=5,
    precision_mode=paddle.inference.PrecisionType.Float32
)
```

### 3. 批处理
处理多个视频时使用批处理可以提高效率

## 下一步

- 查看 [API文档](api.md) 了解详细接口
- 查看 [架构文档](architecture.md) 了解系统设计
- 查看 [训练指南](training.md) 学习模型训练

## 获取帮助

如遇到问题，请：
1. 查看项目Issue
2. 提交新的Issue并附上错误信息
3. 联系项目维护者

---

祝你使用愉快！🎉
