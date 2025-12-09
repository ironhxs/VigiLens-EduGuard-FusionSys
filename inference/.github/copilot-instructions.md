# PaddleVideo Violence Detection Inference System

## Project Overview
This is a **video violence detection inference system** built on PaddleVideo's VideoSwin Transformer model. It provides both a Gradio web UI and Flask REST API for classifying videos as violent (class 1) or non-violent (class 0).

## Architecture & Key Components

### Core Files
- **`api.py`**: Dual-server application running Gradio (port 7860) + Flask API (port 8080) concurrently using threading
- **`infer.py`**: Standalone Gradio interface without Flask API (simpler deployment)
- **`generate_config.py`**: Generates PaddleVideo YAML config files for VideoSwin model training/inference
- **`fix_paddlevideo.sh`**: Bash script that patches PaddleVideo's `sample.py` to handle short videos dynamically

### Model Assets
- **`VideoSwin.json`**: Paddle inference model structure (JSON format)
- **`VideoSwin.pdiparams`**: Model weights file
- Configuration references paths like `/home/aistudio/data/configs/violence_detection/videoswin_violence.yaml`

## Critical Implementation Patterns

### 1. Dual Preprocessing Strategy (Fallback Pattern)
Both `api.py` and `infer.py` implement a **try-fallback** approach:

```python
try:
    # Method 1: Use PaddleVideo's inference_helper.preprocess_batch()
    batched_inputs = inference_helper.preprocess_batch(files)
except Exception:
    # Method 2: Custom preprocess_video() function with manual frame sampling
    video_data = preprocess_video(video_file, num_seg=1, seg_len=32, ...)
```

**Why?** PaddleVideo's preprocessor may fail on short videos or unusual formats. The custom `preprocess_video()` handles:
- Videos with fewer frames than required (32 frames default) via loop sampling
- Uniform frame sampling using `np.linspace()`
- Manual BGR→RGB conversion, resizing (short_size=256), center cropping (target_size=224), and normalization

### 2. Video Format Conversion Pipeline
WebM videos must be converted to MP4 before inference:

```python
if ext == '.webm':
    if check_ffmpeg():
        convert_webm_to_mp4()  # ffmpeg preferred
    else:
        convert_video_with_opencv()  # fallback using cv2.VideoWriter
```

### 3. Model Input Shape Convention
Expected input tensor shape: `[batch=1, channels=3, frames=32, height=224, width=224]`

- Frame transformation order: `HWC → CHW` via `np.transpose((2,0,1))`
- Final assembly: Stack frames → transpose → add batch dimension

### 4. Output Parsing Pattern
Inference output is captured from stdout using `io.StringIO()` and parsed via regex:

```python
class_pattern = r"top-1 class:\s*(\d+)"
score_pattern = r"top-1 score:\s*([0-9.]+)"
```

Class 1 = violent, Class 0 = non-violent

## Development Environment Assumptions

### Hard-coded Paths (Update for Windows/Local)
The codebase assumes Linux AIStudio environment:
```python
DEFAULT_CONFIG = '/home/aistudio/data/configs/violence_detection/videoswin_violence.yaml'
DEFAULT_MODEL_FILE = '/home/aistudio/inference/VideoSwin_base/VideoSwin.json'
DEFAULT_PARAMS_FILE = '/home/aistudio/inference/VideoSwin_base/VideoSwin.pdiparams'
```

Adjust these paths in your `.env` or at file top when running locally.

### Dependency Paths
```python
sys.path.append('/home/aistudio/data/PaddleVideo-develop/paddlevideo/utils')
sys.path.append('/home/aistudio/data/PaddleVideo-develop/tools')
```

Ensure PaddleVideo is cloned/installed and paths are corrected for your environment.

## Running the Application

### Gradio Only (Simpler)
```bash
python infer.py
```
Access at `http://localhost:7860`

### Gradio + Flask API (Production)
```bash
python api.py
```
- Gradio UI: `http://localhost:7860`
- REST API: `http://localhost:8080/api/detect_violence` (POST video file as `multipart/form-data` with key `video`)

API returns JSON:
```json
{
  "is_violent": true,
  "class_id": 1,
  "confidence": 92.5,
  "result_text": "暴力行为",
  "status": "success"
}
```

## Common Modifications

### Change Inference Parameters
Edit the config or pass to `preprocess_video()`:
- `num_seg=1`: Number of video segments
- `seg_len=32`: Frames per segment
- `short_size=256`: Resize shortest edge to this
- `target_size=224`: Final crop size

### Fix Short Video Handling
Run `fix_paddlevideo.sh` to patch PaddleVideo's sampling logic (adjusts `seg_len` dynamically when frames < required).

### Enable GPU Inference
In `create_paddle_predictor()`:
```python
config.enable_use_gpu(8000, 0)  # 8000MB memory, GPU 0
```

## Troubleshooting

- **"无法打开视频"**: Check video codec support; try converting to MP4 with ffmpeg first
- **Model path errors**: Verify `VideoSwin.json` and `.pdiparams` exist at specified paths
- **Import errors**: Ensure PaddleVideo is in `sys.path` and all dependencies installed
- **Short videos fail**: Apply `fix_paddlevideo.sh` patch or use custom preprocessing fallback
