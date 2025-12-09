#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PaddleVideo 暴力检测系统 - Windows 本地运行脚本
适用于 Windows 环境

用途：直接启动推理服务
"""

import sys
import os
import subprocess

def main():
    """主函数：启动推理服务"""
    
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   PaddleVideo 暴力检测系统 - Windows 版本             ║
    ║                                                        ║
    ║   基于 VideoSwin Transformer 的视频暴力内容检测       ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查必要文件
    required_files = [
        os.path.join(current_dir, 'infer.py'),
        os.path.join(current_dir, 'VideoSwin.json'),
        os.path.join(current_dir, 'VideoSwin.pdiparams')
    ]
    
    print("\n检查必要文件...")
    all_exists = True
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {os.path.basename(file)}")
        else:
            print(f"  ✗ {os.path.basename(file)} - 缺失！")
            all_exists = False
    
    if not all_exists:
        print("\n错误：缺少必要文件，请检查！")
        return
    
    print("\n" + "="*60)
    print("启动 Gradio 推理服务...")
    print("="*60)
    print(f"\n服务器地址: http://localhost:7860")
    print("提示: 按 Ctrl+C 停止服务\n")
    
    try:
        # 启动推理服务
        subprocess.run([sys.executable, os.path.join(current_dir, 'infer.py')])
    except KeyboardInterrupt:
        print("\n\n服务已停止")

if __name__ == "__main__":
    main()
