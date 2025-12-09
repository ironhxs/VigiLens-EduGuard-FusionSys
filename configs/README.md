# 配置文件目录

此目录存放项目的各种配置文件。

## 配置文件说明

### violence_detection.yaml
视频暴力检测的主配置文件

```yaml
# 模型配置
model:
  name: VideoSwin
  backbone: Swin-Base
  num_classes: 2
  pretrained: models/VideoSwin/VideoSwin.pdiparams

# 数据配置
data:
  batch_size: 8
  num_workers: 4
  video_format: ['.mp4', '.avi', '.mov']

# 训练配置
training:
  epochs: 100
  learning_rate: 0.001
  optimizer: AdamW
  scheduler: CosineAnnealingLR

# 推理配置
inference:
  batch_size: 1
  num_seg: 1
  seg_len: 32
  threshold: 0.5

# 预处理配置
preprocessing:
  short_size: 256
  target_size: 224
  mean: [0.485, 0.456, 0.406]
  std: [0.229, 0.224, 0.225]
  sampling_method: uniform  # uniform or dense
```

### 其他配置

- `api_config.yaml`: API服务配置
- `deploy_config.yaml`: 部署配置
- `logging_config.yaml`: 日志配置

## 使用方法

```python
from paddlevideo.utils import get_config

# 加载配置
cfg = get_config('configs/violence_detection.yaml')

# 访问配置项
model_name = cfg.model.name
batch_size = cfg.data.batch_size
```

## 配置覆盖

命令行参数可以覆盖配置文件：

```bash
python train.py --config configs/violence_detection.yaml \
                --learning_rate 0.0001 \
                --batch_size 16
```
