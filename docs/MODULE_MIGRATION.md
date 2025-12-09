# 🔄 项目结构更新说明

## 📌 重要更新

本项目已完成代码模块化重构,将 Jupyter Notebooks 中的代码提取为独立的 Python 模块。

---

## 🗂️ 新的项目结构

```
VigiLens-EduGuard-FusionSys/
│
├── src/                        # ⭐ 核心源代码（新增）
│   ├── audio/                 # 音频暴力检测模块
│   │   ├── __init__.py
│   │   ├── config.py          # 配置管理
│   │   ├── data_preprocessing.py  # 数据预处理
│   │   ├── dataset.py         # 数据集和加载器
│   │   ├── model.py           # HTSAT Swin Transformer
│   │   ├── trainer.py         # 训练逻辑
│   │   ├── inference.py       # 推理接口
│   │   └── train.py           # 训练入口脚本
│   │
│   └── video/                 # 视频暴力检测模块（待整理）
│
├── notebooks/                  # 📓 Jupyter Notebooks（重新组织）
│   ├── README.md
│   ├── audio_training_main.ipynb
│   ├── audio_training_backup.ipynb
│   ├── video_inference_demo.ipynb
│   └── ...
│
├── inference/                  # 推理服务
│   ├── api.py                 # Flask API
│   ├── infer.py               # 推理脚本
│   └── ...
│
├── Train/                      # 训练结果和可视化
│   ├── 训练过程.png
│   ├── 测试集评估.png
│   └── README.md
│
├── docs/                       # 文档
├── models/                     # 模型权重
├── data/                       # 数据目录
└── ...
```

---

## 🎯 主要改进

### 1. 代码模块化
- ✅ 从 Notebooks 提取核心代码
- ✅ 创建可复用的 Python 模块
- ✅ 清晰的模块职责划分
- ✅ 支持命令行参数配置

### 2. 项目组织
- ✅ 所有 Notebooks 移至 `notebooks/` 目录
- ✅ 核心代码集中在 `src/` 目录
- ✅ 更清晰的目录结构
- ✅ 完善的文档说明

### 3. 生产就绪
- ✅ 适合自动化部署
- ✅ 支持 CI/CD 集成
- ✅ 更容易进行单元测试
- ✅ 更好的版本控制

---

## 🚀 使用方式对比

### 音频训练

#### ❌ 旧方式 (Notebook)
```bash
jupyter notebook main.ipynb
# 然后手动运行每个单元格...
```

#### ✅ 新方式 (模块化脚本) - 推荐
```bash
python src/audio/train.py \
    --data_dir ./audio \
    --batch_size 16 \
    --num_epochs 50 \
    --learning_rate 1e-4 \
    --use_gpu
```

### 音频推理

#### ❌ 旧方式 (Notebook)
```python
# 需要在 Notebook 中手动执行多个单元格
# 代码分散，不易维护
```

#### ✅ 新方式 (模块化接口) - 推荐
```python
from src.audio.inference import AudioClassifier
from src.audio.config import AudioConfig

config = AudioConfig()
classifier = AudioClassifier(
    model_path='./saved_audio_models/best_model.pdparams',
    config=config
)

# 单个预测
label, confidence, class_name = classifier.predict('test.wav')
print(f"预测: {class_name} (置信度: {confidence:.4f})")

# 批量预测
results = classifier.predict_batch(['audio1.wav', 'audio2.wav'])
```

---

## 📦 模块说明

### `src/audio/config.py`
配置管理类,包含所有超参数和路径配置。

```python
from src.audio.config import AudioConfig

config = AudioConfig()
config.batch_size = 32
config.learning_rate = 1e-4
```

### `src/audio/data_preprocessing.py`
数据预处理工具,音频加载、重采样、填充/裁剪。

```python
from src.audio.data_preprocessing import AudioPreprocessor

preprocessor = AudioPreprocessor(config)
preprocessor.create_processed_dataset()
```

### `src/audio/dataset.py`
Paddle 数据集类和数据加载器。

```python
from src.audio.dataset import create_dataloaders

train_loader, val_loader, test_loader = create_dataloaders(
    train_data, val_data, test_data, config
)
```

### `src/audio/model.py`
HTSAT Swin Transformer 模型架构。

```python
from src.audio.model import HTSAT_Swin_Transformer

model = HTSAT_Swin_Transformer(config)
```

### `src/audio/trainer.py`
训练器类,封装完整的训练流程。

```python
from src.audio.trainer import AudioTrainer

trainer = AudioTrainer(model, config)
best_val_acc, test_acc = trainer.train(train_loader, val_loader, test_loader)
```

### `src/audio/inference.py`
推理接口,模型加载和预测。

```python
from src.audio.inference import AudioClassifier

classifier = AudioClassifier(model_path, config)
label, confidence, class_name = classifier.predict('audio.wav')
```

---

## 🔧 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 训练模型
```bash
# 使用默认参数
python src/audio/train.py

# 自定义参数
python src/audio/train.py \
    --data_dir ./my_audio_data \
    --batch_size 32 \
    --num_epochs 100 \
    --learning_rate 5e-5 \
    --model_save_dir ./my_models \
    --use_gpu

# 查看所有参数
python src/audio/train.py --help
```

### 3. 使用推理
```python
from src.audio.inference import AudioClassifier
from src.audio.config import AudioConfig

# 初始化
config = AudioConfig()
classifier = AudioClassifier(
    model_path='./saved_audio_models/best_model.pdparams',
    config=config
)

# 预测
label, confidence, class_name = classifier.predict('test.wav')
print(f"{class_name}: {confidence:.2%}")
```

---

## 📓 Notebooks 仍然可用

Notebooks 已移动到 `notebooks/` 目录,用于:
- 🔬 实验和原型开发
- 📊 数据探索和可视化
- 📖 教学和演示
- 🐛 交互式调试

详见: [`notebooks/README.md`](notebooks/README.md)

---

## 🎓 开发工作流

```
1. 实验阶段
   └─ 使用 Notebooks 快速原型开发
      └─ notebooks/audio_training_main.ipynb

2. 验证阶段
   └─ 提取验证通过的代码为模块
      └─ src/audio/*.py

3. 生产阶段
   └─ 使用模块化脚本部署
      └─ python src/audio/train.py
      └─ Docker / API / 自动化训练
```

---

## ⚙️ 配置管理

所有配置集中在 `src/audio/config.py`:

```python
class AudioConfig:
    # 训练参数
    batch_size = 16
    num_epochs = 50
    learning_rate = 1e-4
    
    # 音频参数
    sample_rate = 32000
    audio_length = 320000
    
    # 模型参数
    num_classes = 2
    spec_size = 256
    patch_size = 4
    # ...
```

可以通过命令行参数覆盖:
```bash
python src/audio/train.py --batch_size 32 --learning_rate 5e-5
```

---

## 🧪 测试

```bash
# 测试数据预处理
python -c "from src.audio.data_preprocessing import AudioPreprocessor; print('OK')"

# 测试模型创建
python -c "from src.audio.model import HTSAT_Swin_Transformer; print('OK')"

# 测试推理
python -c "from src.audio.inference import AudioClassifier; print('OK')"
```

---

## 📚 相关文档

- [快速开始指南](docs/quickstart.md)
- [架构设计文档](docs/architecture.md)
- [API 接口文档](docs/api.md)
- [Notebooks 使用说明](notebooks/README.md)
- [训练结果说明](Train/README.md)

---

## 🤝 贡献指南

1. 新功能开发: 在 `notebooks/` 中实验
2. 代码稳定后: 提取到 `src/` 模块
3. 添加文档和测试
4. 提交 Pull Request

---

## 📞 支持

- 📧 Email: [your-email]
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/VigiLens-EduGuard-FusionSys/issues)
- 📖 Wiki: [项目 Wiki](https://github.com/yourusername/VigiLens-EduGuard-FusionSys/wiki)

---

**更新日期**: 2024-01
**版本**: 2.0.0 - 模块化重构版本
