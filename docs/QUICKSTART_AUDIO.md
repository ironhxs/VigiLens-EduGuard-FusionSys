# 🚀 快速开始 - 音频模块

这是一个快速指南,帮助您立即开始使用音频暴力检测模块。

---

## 📦 安装

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/VigiLens-EduGuard-FusionSys.git
cd VigiLens-EduGuard-FusionSys

# 2. 安装依赖
pip install -r requirements.txt

# 3. (可选) 安装 PaddlePaddle GPU 版本
pip install paddlepaddle-gpu
```

---

## 🎓 训练模型

### 方法 1: 使用命令行脚本（推荐）

```bash
# 基础训练
python src/audio/train.py \
    --data_dir ./audio \
    --batch_size 16 \
    --num_epochs 50 \
    --use_gpu

# 自定义训练
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

### 方法 2: 使用 Python API

```python
from src.audio.config import AudioConfig
from src.audio.data_preprocessing import AudioPreprocessor
from src.audio.dataset import create_dataloaders
from src.audio.model import HTSAT_Swin_Transformer
from src.audio.trainer import AudioTrainer

# 1. 创建配置
config = AudioConfig()
config.data_dir = './audio'
config.num_epochs = 50

# 2. 预处理数据
preprocessor = AudioPreprocessor(config)
train_data, val_data, test_data = preprocessor.load_and_split_dataset()

# 3. 创建数据加载器
train_loader, val_loader, test_loader = create_dataloaders(
    train_data, val_data, test_data, config
)

# 4. 创建模型和训练
model = HTSAT_Swin_Transformer(config)
trainer = AudioTrainer(model, config)
best_acc, test_acc = trainer.train(train_loader, val_loader, test_loader)
```

### 方法 3: 使用 Jupyter Notebook

```bash
jupyter notebook notebooks/audio_training_main.ipynb
```

---

## 🔮 推理/预测

### 单个音频预测

```python
from src.audio.inference import AudioClassifier
from src.audio.config import AudioConfig

# 初始化分类器
config = AudioConfig()
classifier = AudioClassifier(
    model_path='./saved_audio_models/best_model.pdparams',
    config=config
)

# 预测
label, confidence, class_name = classifier.predict('test.wav')
print(f"预测结果: {class_name}")
print(f"置信度: {confidence:.2%}")
```

### 批量预测

```python
# 批量预测多个音频文件
audio_files = ['audio1.wav', 'audio2.wav', 'audio3.wav']
results = classifier.predict_batch(audio_files)

for result in results:
    print(f"{result['path']}: {result['class_name']} ({result['confidence']:.2%})")
```

---

## 📁 数据格式

### 训练数据结构

```
audio/
├── violence/           # 暴力音频
│   ├── audio1.wav
│   ├── audio2.wav
│   └── ...
└── non_violence/       # 非暴力音频
    ├── audio1.wav
    ├── audio2.wav
    └── ...
```

### 音频要求

- **格式**: WAV, MP3
- **采样率**: 自动重采样到 32kHz
- **声道**: 自动转为单声道
- **长度**: 自动填充/裁剪到 10 秒

---

## 🎯 快速示例

### 完整示例脚本

```bash
# 运行训练示例
python example_usage.py --mode train

# 运行推理示例
python example_usage.py --mode inference
```

### 5分钟快速测试

```bash
# 1. 准备小数据集 (每类 10-20 个音频)
mkdir -p audio/violence audio/non_violence
# ... 放入音频文件 ...

# 2. 快速训练 (5个epoch测试)
python src/audio/train.py \
    --data_dir ./audio \
    --num_epochs 5 \
    --batch_size 8

# 3. 测试推理
python -c "
from src.audio.inference import AudioClassifier
from src.audio.config import AudioConfig

classifier = AudioClassifier(
    './saved_audio_models/best_model.pdparams',
    AudioConfig()
)
result = classifier.predict('audio/violence/sample.wav')
print(f'预测: {result[2]} (置信度: {result[1]:.2%})')
"
```

---

## 🔧 配置参数

### 主要训练参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--data_dir` | `./audio` | 音频数据目录 |
| `--batch_size` | `16` | 批次大小 |
| `--num_epochs` | `50` | 训练轮数 |
| `--learning_rate` | `1e-4` | 学习率 |
| `--use_gpu` | `False` | 是否使用GPU |

### 查看所有参数

```bash
python src/audio/train.py --help
```

---

## 📊 训练监控

训练过程会自动打印:
- 每个 batch 的损失和准确率
- 每个 epoch 的训练/验证指标
- 学习率变化
- 最佳模型保存提示

```
Epoch 1/50 结果:
训练集 - 损失: 0.4532, 准确率: 0.7820
验证集 - 损失: 0.3891, 准确率: 0.8350
学习率: 0.000100 -> 0.000100
保存新的最佳模型! 验证准确率: 0.8350
```

---

## 🐛 常见问题

### Q: 训练时显示 "No module named 'src'"
**A**: 确保在项目根目录运行,或设置 PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Q: 音频文件加载失败
**A**: 确保安装了 librosa:
```bash
pip install librosa soundfile
```

### Q: GPU 训练报错
**A**: 检查 CUDA 版本并安装对应的 PaddlePaddle:
```bash
# CUDA 11.2
pip install paddlepaddle-gpu==2.4.0 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
```

### Q: 内存不足
**A**: 减小 batch_size:
```bash
python src/audio/train.py --batch_size 8
```

---

## 📚 更多资源

- 📖 [完整文档](docs/)
- 📓 [Notebooks 教程](notebooks/README.md)
- 🏗️ [架构设计](docs/architecture.md)
- 🔄 [模块化迁移指南](docs/MODULE_MIGRATION.md)
- 📝 [API 文档](docs/api.md)

---

## 🤝 获取帮助

- 💬 [GitHub Issues](https://github.com/yourusername/VigiLens-EduGuard-FusionSys/issues)
- 📧 Email: your-email@example.com
- 📖 [Wiki](https://github.com/yourusername/VigiLens-EduGuard-FusionSys/wiki)

---

## ⭐ 下一步

1. ✅ 按上述步骤训练你的第一个模型
2. ✅ 使用推理接口测试模型效果
3. ✅ 阅读完整文档了解更多功能
4. ✅ 根据需求调整配置参数
5. ✅ 在实际数据上评估性能

---

**开始你的音频暴力检测之旅吧! 🚀**
