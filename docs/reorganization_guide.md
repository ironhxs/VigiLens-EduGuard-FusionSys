# 项目整理指南

本文档说明如何完成项目文件的重新组织。

## 当前状态

项目已创建新的目录结构，但原有文件仍在旧位置。

## 需要执行的操作

### 1. 移动推理相关代码

将 `inference/` 目录下的Python文件移动到 `src/inference/`：

```powershell
# 移动推理脚本
Move-Item -Path "inference\api.py" -Destination "src\inference\" -Force
Move-Item -Path "inference\infer.py" -Destination "src\inference\" -Force
Move-Item -Path "inference\generate_config.py" -Destination "src\inference\" -Force
Move-Item -Path "inference\run_local.py" -Destination "src\inference\" -Force
Move-Item -Path "inference\setup_and_run.py" -Destination "src\inference\" -Force

# 移动shell脚本（如果需要）
Move-Item -Path "inference\fix_paddlevideo.sh" -Destination "src\inference\" -Force
```

### 2. 移动模型文件

将模型文件移动到 `models/VideoSwin/`：

```powershell
# 创建VideoSwin目录
New-Item -Path "models\VideoSwin" -ItemType Directory -Force

# 移动模型文件
Move-Item -Path "inference\VideoSwin.json" -Destination "models\VideoSwin\" -Force
Move-Item -Path "inference\VideoSwin.pdiparams" -Destination "models\VideoSwin\" -Force
```

### 3. 移动Notebook

Notebook已经复制到 `notebooks/` 目录，原文件可以保留或删除：

```powershell
# 如果要删除原文件
# Remove-Item -Path "inference\main_3.ipynb" -Force
```

### 4. 整理文档

```powershell
# 如果存在计算机视觉想法文档，移动到docs
# Move-Item -Path "计算机视觉想法.md" -Destination "docs\ideas.md" -Force

# 删除空的项目文档
Remove-Item -Path "VigiLens-EduGuard-FusionSys.md" -Force
```

### 5. 整理申报材料

```powershell
# 保持申报目录不变
# 申报/ 目录保留原样
```

### 6. 清理旧目录

移动完成后，可以删除空的 `inference/` 目录：

```powershell
# 确认目录为空后删除
Remove-Item -Path "inference" -Recurse -Force
```

## 更新代码中的路径引用

移动文件后，需要更新代码中的路径引用。

### 在 src/inference/*.py 中更新路径

```python
# 旧路径（需要更新）
DEFAULT_MODEL_FILE = '/home/aistudio/inference/VideoSwin_base/VideoSwin.json'
DEFAULT_PARAMS_FILE = '/home/aistudio/inference/VideoSwin_base/VideoSwin.pdiparams'

# 新路径
DEFAULT_MODEL_FILE = 'models/VideoSwin/VideoSwin.json'
DEFAULT_PARAMS_FILE = 'models/VideoSwin/VideoSwin.pdiparams'
```

### 更新 sys.path

```python
# 旧代码
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 新代码（如果从src/inference运行）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
```

## 验证整理结果

### 1. 检查目录结构

```powershell
tree /F
```

期望的结构：
```
VigiLens-EduGuard-FusionSys/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── requirements.txt
├── .gitignore
├── docs/
│   ├── architecture.md
│   ├── quickstart.md
│   ├── api.md
│   └── ideas.md (如果存在)
├── src/
│   ├── inference/
│   │   ├── api.py
│   │   ├── infer.py
│   │   ├── generate_config.py
│   │   ├── run_local.py
│   │   └── setup_and_run.py
│   └── utils/
├── models/
│   ├── README.md
│   └── VideoSwin/
│       ├── VideoSwin.json
│       └── VideoSwin.pdiparams
├── configs/
│   └── README.md
├── data/
│   └── README.md
├── notebooks/
│   └── main_3.ipynb
├── PaddleVideo-develop/
├── research/
└── 申报/
```

### 2. 测试代码运行

```powershell
# 测试API
cd src/inference
python api.py

# 测试推理
python infer.py
```

### 3. 检查导入路径

确保所有Python模块都能正确导入：

```python
# 测试导入
python -c "from src.inference import api"
```

## 注意事项

1. **备份重要文件**：在移动文件前，建议先备份
2. **更新路径**：移动后务必更新代码中的路径引用
3. **测试功能**：确保所有功能正常工作
4. **Git提交**：完成整理后提交到版本控制

## 快速执行脚本

创建 `reorganize.ps1` 脚本一键执行所有操作：

```powershell
# reorganize.ps1
Write-Host "开始整理项目..." -ForegroundColor Green

# 1. 移动推理代码
Write-Host "移动推理代码..." -ForegroundColor Yellow
Move-Item -Path "inference\*.py" -Destination "src\inference\" -Force

# 2. 移动模型文件
Write-Host "移动模型文件..." -ForegroundColor Yellow
New-Item -Path "models\VideoSwin" -ItemType Directory -Force
Move-Item -Path "inference\VideoSwin.*" -Destination "models\VideoSwin\" -Force -ErrorAction SilentlyContinue

# 3. 清理
Write-Host "清理旧目录..." -ForegroundColor Yellow
Remove-Item -Path "VigiLens-EduGuard-FusionSys.md" -Force -ErrorAction SilentlyContinue

Write-Host "整理完成！" -ForegroundColor Green
Write-Host "请手动更新代码中的路径引用。" -ForegroundColor Cyan
```

运行脚本：
```powershell
.\reorganize.ps1
```

## 后续步骤

1. 完成文件移动
2. 更新路径引用
3. 测试所有功能
4. 提交到Git
5. 更新文档（如有新的路径变化）

---

整理完成后，项目结构将更加清晰规范！
