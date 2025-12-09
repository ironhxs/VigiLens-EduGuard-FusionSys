# 📁 项目目录说明

## 根目录文件（核心）

| 文件 | 说明 |
|------|------|
| `README.md` | 项目主文档 |
| `LICENSE` | MIT 开源协议 |
| `CHANGELOG.md` | 版本更新日志 |
| `CONTRIBUTING.md` | 贡献指南 |
| `requirements.txt` | Python 依赖 |
| `.gitignore` | Git 忽略规则 |

## 核心目录

| 目录 | 用途 | README |
|------|------|--------|
| `src/` | 生产代码(音频/视频模块) | ✅ |
| `inference/` | 视频推理服务 | ✅ |
| `examples/` | 示例代码 | ✅ |
| `notebooks/` | Jupyter Notebooks | ✅ |
| `docs/` | 完整文档 | ✅ |
| `Train/` | 训练结果 | ✅ |
| `models/` | 模型权重 | ✅ |
| `scripts/` | 工具脚本 | ✅ |
| `data/` | 数据目录 | ✅ |
| `configs/` | 配置文件 | ✅ |
| `assets/` | 资源文件 | - |

## 快速导航

### 🚀 开始使用
- [快速开始指南](docs/quickstart.md)
- [音频模块快速开始](docs/QUICKSTART_AUDIO.md)
- [示例代码](examples/)

### 📚 学习文档
- [架构设计](docs/architecture.md)
- [API 文档](docs/api.md)
- [Notebooks 教程](notebooks/README.md)

### 🔧 开发维护
- [贡献指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)
- [工具脚本](scripts/)
- [项目状态记录](docs/project-status/)

### 🎓 训练和模型
- [训练指南](Train/README.md)
- [模型说明](models/README.md)
- [数据准备](data/README.md)

## 目录层次结构

```
VigiLens-EduGuard-FusionSys/
│
├── 核心文件 (6个)
│   ├── README.md
│   ├── LICENSE
│   ├── CHANGELOG.md
│   ├── CONTRIBUTING.md
│   ├── requirements.txt
│   └── .gitignore
│
├── 源代码 (2个)
│   ├── src/          # 模块化代码
│   └── inference/    # 推理服务
│
├── 文档和示例 (3个)
│   ├── docs/         # 完整文档
│   ├── examples/     # 示例代码
│   └── notebooks/    # Jupyter Notebooks
│
├── 数据和模型 (3个)
│   ├── models/       # 模型权重
│   ├── data/         # 数据目录
│   └── Train/        # 训练结果
│
└── 配置和工具 (3个)
    ├── configs/      # 配置文件
    ├── scripts/      # 工具脚本
    └── assets/       # 资源文件
```

## 文件组织原则

### ✅ 保留在根目录
- **必要文件**: README, LICENSE, requirements.txt
- **重要文档**: CHANGELOG, CONTRIBUTING
- **配置文件**: .gitignore

### 📂 归类到子目录
- **状态文档** → `docs/project-status/`
- **示例代码** → `examples/`
- **工具脚本** → `scripts/`
- **快速指南** → `docs/`

### 🗑️ 不保留
- 临时文件
- 重复文档
- 过时脚本
- 构建产物

## 维护建议

1. **根目录保持整洁**: 只保留核心文件和目录
2. **文档分类管理**: 按用途放入对应子目录
3. **README 完善**: 每个子目录都应有 README
4. **定期清理**: 移除过时和冗余文件

---

**最后更新**: 2024年1月  
**项目结构版本**: v2.0.0
