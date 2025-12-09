# API文档

## 概述

VigiLens-EduGuard-FusionSys 提供RESTful API接口，支持视频暴力行为检测。

**Base URL**: `http://localhost:5000`

## 认证

当前版本不需要认证（开发环境）。生产环境应添加API Key或Token认证。

## API端点

### 1. 健康检查

检查服务是否正常运行。

**端点**: `GET /health`

**请求示例**:
```bash
curl http://localhost:5000/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. 单视频预测

上传单个视频进行暴力行为检测。

**端点**: `POST /predict`

**请求参数**:
- `video` (file, required): 视频文件
- `threshold` (float, optional): 判定阈值，默认0.5

**请求示例**:
```bash
curl -X POST http://localhost:5000/predict \
  -F "video=@/path/to/video.mp4" \
  -F "threshold=0.6"
```

**Python示例**:
```python
import requests

url = "http://localhost:5000/predict"
files = {'video': open('test.mp4', 'rb')}
data = {'threshold': 0.6}
response = requests.post(url, files=files, data=data)
print(response.json())
```

**响应示例**:
```json
{
  "success": true,
  "video_name": "test.mp4",
  "prediction": {
    "class": "violence",
    "class_id": 1,
    "confidence": 0.8542
  },
  "is_violence": true,
  "threshold": 0.6,
  "processing_time": 2.34,
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "No video file provided",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**状态码**:
- `200 OK`: 成功
- `400 Bad Request`: 请求参数错误
- `500 Internal Server Error`: 服务器错误

### 3. 批量预测

上传多个视频进行批量检测。

**端点**: `POST /batch_predict`

**请求参数**:
- `videos[]` (files, required): 多个视频文件
- `threshold` (float, optional): 判定阈值，默认0.5

**请求示例**:
```bash
curl -X POST http://localhost:5000/batch_predict \
  -F "videos[]=@video1.mp4" \
  -F "videos[]=@video2.mp4" \
  -F "threshold=0.6"
```

**Python示例**:
```python
import requests

url = "http://localhost:5000/batch_predict"
files = [
    ('videos[]', open('video1.mp4', 'rb')),
    ('videos[]', open('video2.mp4', 'rb'))
]
data = {'threshold': 0.6}
response = requests.post(url, files=files, data=data)
print(response.json())
```

**响应示例**:
```json
{
  "success": true,
  "results": [
    {
      "video_name": "video1.mp4",
      "prediction": {
        "class": "violence",
        "class_id": 1,
        "confidence": 0.8542
      },
      "is_violence": true
    },
    {
      "video_name": "video2.mp4",
      "prediction": {
        "class": "normal",
        "class_id": 0,
        "confidence": 0.9123
      },
      "is_violence": false
    }
  ],
  "total": 2,
  "violence_count": 1,
  "processing_time": 5.67,
  "timestamp": "2024-01-15T10:40:00Z"
}
```

### 4. 获取模型信息

获取当前使用的模型信息。

**端点**: `GET /model_info`

**请求示例**:
```bash
curl http://localhost:5000/model_info
```

**响应示例**:
```json
{
  "success": true,
  "model": {
    "name": "VideoSwin",
    "version": "base",
    "input_shape": [1, 3, 32, 224, 224],
    "num_classes": 2,
    "classes": ["normal", "violence"]
  },
  "config": {
    "num_seg": 1,
    "seg_len": 32,
    "target_size": 224
  }
}
```

### 5. 视频URL预测

通过视频URL进行预测（无需上传文件）。

**端点**: `POST /predict_url`

**请求参数**:
- `url` (string, required): 视频URL
- `threshold` (float, optional): 判定阈值，默认0.5

**请求示例**:
```bash
curl -X POST http://localhost:5000/predict_url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4", "threshold": 0.6}'
```

**Python示例**:
```python
import requests

url = "http://localhost:5000/predict_url"
data = {
    "url": "https://example.com/video.mp4",
    "threshold": 0.6
}
response = requests.post(url, json=data)
print(response.json())
```

**响应格式**: 与 `/predict` 相同

## 数据格式

### 类别说明

| class_id | class_name | 描述 |
|----------|------------|------|
| 0 | normal | 正常行为 |
| 1 | violence | 暴力行为 |

### 置信度说明

- `confidence`: 模型预测的置信度，范围 [0, 1]
- `threshold`: 判定阈值，超过此值判定为暴力行为
- `is_violence`: 是否判定为暴力行为（confidence >= threshold）

## 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 端点不存在 |
| 413 | 文件过大 |
| 415 | 不支持的媒体类型 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

## 限制说明

### 文件大小限制
- 单个视频文件: 最大 200MB
- 批量上传总大小: 最大 500MB

### 视频格式支持
- MP4 (推荐)
- AVI
- MOV
- MKV

### 视频时长建议
- 推荐: 5-60秒
- 最长: 300秒（5分钟）

### 频率限制
- 单IP: 100次/小时（开发环境无限制）

## 使用示例

### 完整工作流示例

```python
import requests
import time

class ViolenceDetectorClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def check_health(self):
        """检查服务健康状态"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def predict(self, video_path, threshold=0.5):
        """单视频预测"""
        url = f"{self.base_url}/predict"
        files = {'video': open(video_path, 'rb')}
        data = {'threshold': threshold}
        response = requests.post(url, files=files, data=data)
        return response.json()
    
    def batch_predict(self, video_paths, threshold=0.5):
        """批量预测"""
        url = f"{self.base_url}/batch_predict"
        files = [('videos[]', open(path, 'rb')) for path in video_paths]
        data = {'threshold': threshold}
        response = requests.post(url, files=files, data=data)
        return response.json()

# 使用示例
if __name__ == "__main__":
    client = ViolenceDetectorClient()
    
    # 检查服务状态
    health = client.check_health()
    print("服务状态:", health)
    
    # 单视频预测
    result = client.predict("test.mp4", threshold=0.6)
    print("预测结果:", result)
    
    # 批量预测
    batch_result = client.batch_predict(
        ["video1.mp4", "video2.mp4"],
        threshold=0.6
    )
    print("批量结果:", batch_result)
```

### 异步处理示例

```python
import asyncio
import aiohttp

async def predict_async(session, video_path):
    """异步预测"""
    url = "http://localhost:5000/predict"
    data = aiohttp.FormData()
    data.add_field('video',
                   open(video_path, 'rb'),
                   filename=video_path)
    
    async with session.post(url, data=data) as response:
        return await response.json()

async def main():
    video_paths = ["video1.mp4", "video2.mp4", "video3.mp4"]
    
    async with aiohttp.ClientSession() as session:
        tasks = [predict_async(session, path) for path in video_paths]
        results = await asyncio.gather(*tasks)
        
        for path, result in zip(video_paths, results):
            print(f"{path}: {result}")

# 运行
asyncio.run(main())
```

## Webhook支持（计划中）

未来版本将支持Webhook，在检测完成后自动推送结果。

```json
{
  "webhook_url": "https://your-domain.com/webhook",
  "events": ["prediction_completed", "violence_detected"]
}
```

## 性能监控

获取API性能指标（需要管理员权限）：

```bash
curl http://localhost:5000/metrics
```

返回Prometheus格式的指标数据。

## 版本历史

- v1.0.0 (2024-01): 初始版本
  - 基础预测API
  - 批量预测
  - 健康检查

## 技术支持

如有API使用问题，请：
1. 查看本文档
2. 提交GitHub Issue
3. 联系技术支持

---

最后更新: 2024年1月15日
