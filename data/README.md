# 数据目录

此目录用于存放项目数据文件。

## 目录结构

```
data/
├── raw/                    # 原始数据
│   ├── videos/            # 原始视频
│   └── annotations/       # 标注文件
├── processed/             # 预处理后的数据
│   ├── train/            # 训练集
│   ├── val/              # 验证集
│   └── test/             # 测试集
├── samples/               # 示例数据
└── README.md             # 本文件
```

## 数据格式

### 视频数据
- 格式: MP4, AVI, MOV
- 分辨率: 建议 ≥ 224x224
- 帧率: 建议 ≥ 25 FPS
- 时长: 建议 5-60秒

### 标注格式
```json
{
  "video_name": "sample.mp4",
  "label": "violence",  // or "normal"
  "start_frame": 0,
  "end_frame": 100,
  "description": "打架场景"
}
```

## 数据集准备

### 1. 数据采集
- 收集校园监控视频（需获得授权）
- 公开数据集（如有）
- 注意隐私保护

### 2. 数据清洗
```bash
python scripts/clean_data.py --input data/raw --output data/processed
```

### 3. 数据标注
使用标注工具对视频进行标注

### 4. 数据划分
```python
# 示例代码
train_ratio = 0.7
val_ratio = 0.15
test_ratio = 0.15
```

## 注意事项

⚠️ **重要提示**:
- 数据文件已通过 `.gitignore` 排除
- 不要将原始数据提交到Git
- 注意保护个人隐私信息
- 遵守数据使用协议

## 数据隐私

- 所有个人身份信息应脱敏处理
- 仅用于研究目的
- 定期清理不必要的数据
- 符合GDPR等隐私法规
