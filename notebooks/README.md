# 📓 Notebooks 目录

本目录包含项目的所有 Jupyter Notebooks,主要用于实验、演示和数据探索。

## 📋 文件说明

### 音频训练相关
- **`audio_training_main.ipynb`** - 音频暴力检测模型训练主 Notebook
  - 包含完整的训练流程: 数据预处理、模型构建、训练和评估
  - HTSAT Swin Transformer 模型实现
  - 训练结果可视化
  
- **`audio_training_backup.ipynb`** - 音频训练的备份版本
  - 实验性代码和调试记录
  
- **`audio_training.ipynb`** - 音频训练简化版本

### 视频推理相关
- **`video_inference_demo.ipynb`** - 视频暴力检测推理演示
  - VideoSwin Transformer 推理示例
  - 包含视频预处理和结果可视化
  
- **`main_3.ipynb`** - 推理实验 Notebook

### 其他
- **`experiment_backup.ipynb`** - 实验备份

---

## 🚀 使用说明

### 1. 环境准备
```bash
# 安装 Jupyter
pip install jupyter notebook

# 或使用 JupyterLab
pip install jupyterlab
```

### 2. 启动 Jupyter
```bash
# 启动 Notebook
jupyter notebook

# 或启动 JupyterLab
jupyter lab
```

### 3. 运行 Notebook
1. 在浏览器中打开对应的 `.ipynb` 文件
2. 按顺序执行单元格 (Shift + Enter)
3. 根据注释修改参数和路径

---

## ⚠️ 重要提示

### 生产环境使用
**这些 notebooks 主要用于实验和演示。如需在生产环境中使用,请使用模块化的 Python 脚本:**

- **音频训练**: 使用 `src/audio/train.py`
- **音频推理**: 使用 `src/audio/inference.py`
- **视频推理**: 使用 `inference/api.py` 或 `inference/infer.py`

### 模块化代码优势
✅ 更好的代码组织和可维护性  
✅ 支持命令行参数配置  
✅ 适合自动化部署和 CI/CD  
✅ 更容易进行单元测试  
✅ 避免 Jupyter 内核状态问题

---

## 📦 代码迁移

Notebook 中的核心功能已提取为模块化代码:

```
notebooks/audio_training_main.ipynb  
    ↓ 提取为
src/audio/
    ├── config.py              # 配置管理
    ├── data_preprocessing.py  # 数据预处理
    ├── dataset.py            # 数据集和加载器
    ├── model.py              # 模型架构
    ├── trainer.py            # 训练逻辑
    ├── inference.py          # 推理接口
    └── train.py              # 训练入口脚本
```

---

## 🔄 从 Notebook 迁移到脚本

### 训练示例
```bash
# Notebook 方式
jupyter notebook notebooks/audio_training_main.ipynb

# 脚本方式 (推荐)
python src/audio/train.py --data_dir ./audio --num_epochs 50 --batch_size 16
```

### 推理示例
```python
# Notebook 方式
# 需要手动运行多个单元格...

# 脚本方式 (推荐)
from src.audio.inference import AudioClassifier

classifier = AudioClassifier(
    model_path='./saved_audio_models/best_model.pdparams',
    config=config
)
label, confidence, class_name = classifier.predict('test.wav')
```

---

## 📊 Notebook 特点

### 优点
- 交互式开发和调试
- 即时可视化结果
- 适合数据探索和实验
- 方便分享和展示

### 缺点
- 不适合生产部署
- 代码重复和难以维护
- 内核状态管理复杂
- 版本控制困难

---

## 🛠️ 最佳实践

1. **实验阶段**: 使用 Notebooks 快速原型开发
2. **验证阶段**: 将验证通过的代码提取为模块
3. **生产阶段**: 使用模块化脚本部署

```
实验 (Notebook) → 模块化 (Python) → 部署 (Docker/API)
```

---

## 📝 维护说明

- **定期清理**: 移除过时的实验 notebooks
- **文档同步**: 更新 notebook 中的注释和说明
- **代码迁移**: 将稳定的代码迁移到 `src/` 目录
- **结果归档**: 保存重要的训练结果和可视化

---

## 📞 联系方式

如有问题或建议,请联系项目维护者或提交 Issue。
