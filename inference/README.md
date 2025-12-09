# 推理模块使用说明

## 📦 模型文件位置

**请将训练好的模型文件放在此目录下：**

```
inference/
├── VideoSwin.json          # 模型结构文件 (必需)
├── VideoSwin.pdiparams     # 模型权重文件 (必需)
├── infer.py                # Gradio界面推理
├── api.py                  # Flask API服务
└── run_local.py            # 命令行推理
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装PaddlePaddle (选择GPU或CPU版本)
pip install paddlepaddle-gpu>=2.2.0  # GPU版本
# pip install paddlepaddle>=2.2.0    # CPU版本

# 安装其他依赖
pip install -r ../requirements.txt
```

### 2. 准备模型文件

将你的模型文件复制到当前目录：
```bash
cp /path/to/your/VideoSwin.json ./
cp /path/to/your/VideoSwin.pdiparams ./
```

### 3. 运行推理

#### 方式一：Web界面（推荐）
```bash
python infer.py
```
打开浏览器访问：http://localhost:7860

#### 方式二：命令行
```bash
python run_local.py --video_path /path/to/video.mp4
```

#### 方式三：API服务
```bash
python api.py
```

## ⚙️ 配置说明

默认配置在各脚本开头：
```python
DEFAULT_MODEL_FILE = './VideoSwin.json'
DEFAULT_PARAMS_FILE = './VideoSwin.pdiparams'
```

如需修改路径，请编辑对应脚本的 `DEFAULT_MODEL_FILE` 和 `DEFAULT_PARAMS_FILE` 变量。

## 📝 模型输入要求

- **帧数**: 32帧
- **尺寸**: 224x224
- **格式**: RGB
- **归一化**: [0, 1] 范围

## ❓ 常见问题

### Q: 模型文件从哪里获取？
A: 
- 训练好的模型在 `Train/output/` 目录
- 或从训练日志中查找导出的模型路径

### Q: 支持哪些视频格式？
A: 支持常见格式如 mp4, avi, mov 等，通过OpenCV读取

### Q: 推理速度慢怎么办？
A: 
- 使用GPU版本PaddlePaddle
- 减少视频分辨率
- 使用模型量化加速
