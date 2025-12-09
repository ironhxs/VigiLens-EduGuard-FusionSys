#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PaddleVideo 暴力检测系统 - 完整安装和运行脚本
从 main_3.ipynb 转换而来

用途：
1. 配置环境路径
2. 检查 CUDA 支持
3. 安装 PaddlePaddle GPU 版本
4. 解压 PaddleVideo 开发包
5. 修复 PaddleVideo 采样问题
6. 生成配置文件
7. 启动推理服务
"""

import sys
import os
import subprocess

# EXPERIMENT: 环境配置
# 添加外部库路径（AIStudio 环境）
sys.path.append('/home/aistudio/external-libraries')

def run_command(cmd, description):
    """执行系统命令并打印结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("警告:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"错误: {e}")
        print(f"输出: {e.stdout}")
        print(f"错误信息: {e.stderr}")
        return False

def main():
    """主函数：按顺序执行所有步骤"""
    
    # STEP 1: 检查 CUDA 支持
    print("\n" + "="*60)
    print("步骤 1/7: 检查 PaddlePaddle CUDA 支持")
    print("="*60)
    run_command(
        'python -c "import paddle; print(paddle.device.is_compiled_with_cuda()); print(paddle.device.cuda.device_count())"',
        "检查 CUDA 是否可用"
    )
    
    # STEP 2: 安装 PaddlePaddle GPU 版本
    print("\n" + "="*60)
    print("步骤 2/7: 安装 PaddlePaddle GPU 3.0.0")
    print("="*60)
    run_command(
        'python -m pip install paddlepaddle-gpu==3.0.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/',
        "安装 PaddlePaddle GPU 版本"
    )
    
    # STEP 3: 解压 PaddleVideo 开发包
    print("\n" + "="*60)
    print("步骤 3/7: 解压 PaddleVideo 开发包")
    print("="*60)
    # NOTE: 需要根据实际路径调整
    run_command(
        'unzip -d /home/aistudio/data /home/aistudio/huitong-zhidun/Swin_video/PaddleVideo-develop.zip',
        "解压 PaddleVideo 到数据目录"
    )
    
    # STEP 4: 修复 PaddleVideo 采样问题
    print("\n" + "="*60)
    print("步骤 4/7: 修复 PaddleVideo 短视频采样问题")
    print("="*60)
    run_command(
        'chmod +x /home/aistudio/huitong-zhidun/Swin_video/fix_paddlevideo.sh',
        "赋予脚本执行权限"
    )
    run_command(
        '/home/aistudio/huitong-zhidun/Swin_video/fix_paddlevideo.sh',
        "执行修复脚本"
    )
    
    # STEP 5: 生成配置文件
    print("\n" + "="*60)
    print("步骤 5/7: 生成 VideoSwin 配置文件")
    print("="*60)
    run_command(
        'python /home/aistudio/huitong-zhidun/Swin_video/generate_config.py',
        "生成暴力检测配置"
    )
    
    # STEP 6: 启动推理服务
    print("\n" + "="*60)
    print("步骤 6/7: 启动 Gradio 推理服务")
    print("="*60)
    print("即将启动推理服务器...")
    print("访问地址: http://localhost:7860")
    run_command(
        'python /home/aistudio/inference/infer.py',
        "启动推理服务"
    )

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   PaddleVideo 暴力检测系统 - 自动安装和运行脚本       ║
    ║                                                        ║
    ║   基于 VideoSwin Transformer 的视频暴力内容检测       ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断执行")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
