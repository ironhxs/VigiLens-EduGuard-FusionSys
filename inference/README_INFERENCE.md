# 推理使用说明

## 🔍 当前问题

你的模型文件格式：
- `VideoSwin.json` - PIR格式（Paddle Intermediate Representation）
- `VideoSwin.pdiparams` - 单个Tensor (shape [128])，不是标准的state_dict

这种格式与标准的Paddle Inference API不兼容，导致段错误。

## ✅ 解决方案

### 方案1：使用原始训练文件（推荐）

如果你有训练输出的原始文件（通常在 `output/` 或 `checkpoints/` 目录）：

```bash
# 查找训练输出
find . -name "*.pdparams" -o -name "best.pd*"

# 使用原始文件进行推理
cd PaddleVideo-develop
python tools/predict.py \
    --config configs/recognition/videoswin/videoswin_violence.yaml \
    --input_file /path/to/video.mp4 \
    --model_file /path/to/best.pdparams
```

### 方案2：重新导出模型

使用PaddleVideo的导出工具：

```bash
cd PaddleVideo-develop
python tools/export_model.py \
    --config configs/recognition/videoswin/videoswin_violence.yaml \
    --weights /path/to/best.pdparams \
    --save_dir ../inference/exported_model
```

这会生成标准的 `model.pdmodel` 和 `model.pdiparams` 文件。

### 方案3：直接使用PaddleVideo推理

最简单的方法 - 不需要导出，直接用训练框架推理：

```python
# 在项目根目录运行
cd /root/autodl-tmp/VigiLens-EduGuard-FusionSys
python -c "
import sys
sys.path.append('PaddleVideo-develop')
from paddlevideo.tasks import predict
from paddlevideo.utils import get_config

cfg = get_config('configs/your_config.yaml')
cfg.INFERENCE.model_file = 'path/to/best.pdparams'

predict.main(cfg, input_file='1.mp4')
"
```

## 📝 需要的信息

请提供以下信息以便我帮你：

1. **训练命令**：你是怎么训练的？
2. **训练输出**：`find . -name "*.pdparams"` 的结果
3. **配置文件**：训练时用的yaml配置文件路径
4. **导出命令**：如何生成这两个文件的？

有了这些信息，我可以为你创建正确的推理脚本！
