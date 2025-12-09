# 贡献指南

感谢你对 VigiLens-EduGuard-FusionSys 项目的关注！

## 如何贡献

### 报告问题

如果你发现了bug或有功能建议：

1. 查看 [Issues](https://github.com/ironhxs/VigiLens-EduGuard-FusionSys/issues) 确认问题是否已存在
2. 如果没有，创建新的Issue
3. 提供详细的问题描述和复现步骤

### 提交代码

1. **Fork 项目**
   ```bash
   # 在GitHub上点击Fork按钮
   ```

2. **克隆你的Fork**
   ```bash
   git clone https://github.com/your-username/VigiLens-EduGuard-FusionSys.git
   cd VigiLens-EduGuard-FusionSys
   ```

3. **创建新分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

4. **进行修改**
   - 遵循项目的代码风格
   - 添加必要的测试
   - 更新相关文档

5. **提交更改**
   ```bash
   git add .
   git commit -m "描述你的更改"
   ```

6. **推送到你的Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **创建Pull Request**
   - 在GitHub上打开Pull Request
   - 描述你的更改和原因
   - 等待代码审查

## 代码规范

### Python代码风格

- 遵循 PEP 8 规范
- 使用4个空格缩进
- 最大行长度120字符
- 使用类型注解

```python
def process_video(video_path: str, threshold: float = 0.5) -> dict:
    """
    处理视频并返回检测结果
    
    Args:
        video_path: 视频文件路径
        threshold: 检测阈值
        
    Returns:
        包含检测结果的字典
    """
    pass
```

### 使用工具检查代码

```bash
# 格式化代码
black src/

# 检查代码质量
flake8 src/

# 类型检查
mypy src/
```

## 提交信息规范

使用清晰的提交信息：

```
<type>: <subject>

<body>

<footer>
```

**Type类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**:
```
feat: 添加音频情绪识别模块

- 实现CNN特征提取
- 集成ConvLSTM时序分析
- 添加相关测试用例

Closes #123
```

## 测试

在提交PR前，确保所有测试通过：

```bash
# 运行测试
pytest tests/

# 测试覆盖率
pytest --cov=src tests/
```

## 文档

- 更新相关的README
- 添加必要的代码注释
- 更新API文档（如适用）

## 行为准则

- 尊重所有贡献者
- 友好交流，建设性反馈
- 关注技术问题，避免人身攻击

## 问题讨论

- 使用Issue讨论功能和bug
- 使用Discussion讨论想法和问题
- 保持主题相关

## 许可证

提交代码即表示你同意将代码贡献到MIT许可证下。

## 获取帮助

如有疑问：
- 查看现有Issues和Discussions
- 创建新的Issue寻求帮助
- 联系项目维护者

---

再次感谢你的贡献！🎉
