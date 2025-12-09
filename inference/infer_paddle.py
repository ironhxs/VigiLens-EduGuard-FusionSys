#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用Paddle动态图直接加载模型（不使用Inference API）
"""

import os
import sys
import cv2
import numpy as np
import gradio as gr
import paddle

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, 'PaddleVideo-develop'))

INFERENCE_DIR = os.path.dirname(os.path.abspath(__file__))
PARAMS_FILE = os.path.join(INFERENCE_DIR, 'VideoSwin.pdiparams')


def preprocess_video(video_path, num_seg=1, seg_len=32, short_size=256, target_size=224):
    """预处理视频"""
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频: {video_path}")
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    target_frames = num_seg * seg_len
    
    # 采样策略
    if total_frames < target_frames:
        indices = np.tile(np.arange(total_frames), int(np.ceil(target_frames / total_frames)))[:target_frames]
    else:
        indices = np.linspace(0, total_frames - 1, target_frames, dtype=int)
    
    # 读取帧
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            frame = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        frames.append(frame)
    cap.release()
    
    # 处理每一帧
    processed_frames = []
    for frame in frames:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 缩放
        height, width = frame.shape[:2]
        scale = short_size / min(height, width)
        new_height, new_width = int(height * scale), int(width * scale)
        frame = cv2.resize(frame, (new_width, new_height))
        
        # 中心裁剪
        start_h = (new_height - target_size) // 2
        start_w = (new_width - target_size) // 2
        frame = frame[start_h:start_h+target_size, start_w:start_w+target_size]
        
        # 归一化
        frame = frame.astype(np.float32) / 255.0
        processed_frames.append(frame)
    
    # 转换为模型输入格式: [1, 3, T, H, W]
    video_data = np.stack(processed_frames, axis=0)  # [T, H, W, 3]
    video_data = video_data.transpose(3, 0, 1, 2)     # [3, T, H, W]
    video_data = video_data[np.newaxis, :]            # [1, 3, T, H, W]
    
    return paddle.to_tensor(video_data, dtype='float32')


def load_model():
    """加载VideoSwin模型"""
    try:
        from paddlevideo.modeling.builder import build_model
        from paddlevideo.utils import get_config
        
        # 尝试从PaddleVideo加载模型定义
        print("尝试使用PaddleVideo加载模型...")
        
        # 简化配置
        class SimpleConfig:
            def __init__(self):
                self.MODEL = type('obj', (object,), {
                    'framework': 'Recognizer3D',
                    'backbone': {
                        'name': 'VideoSwinTransformer',
                        'pretrained': None,
                        'patch_size': (2, 4, 4),
                        'embed_dim': 128,
                        'depths': [2, 2, 18, 2],
                        'num_heads': [4, 8, 16, 32],
                        'window_size': (8, 7, 7),
                    },
                    'head': {
                        'name': 'I3DHead',
                        'num_classes': 2,
                        'in_channels': 1024,
                    }
                })()
        
        cfg = SimpleConfig()
        model = build_model(cfg.MODEL)
        
        # 加载权重
        print(f"加载权重: {PARAMS_FILE}")
        state_dict = paddle.load(PARAMS_FILE)
        model.set_state_dict(state_dict)
        model.eval()
        
        return model
        
    except Exception as e:
        print(f"使用PaddleVideo加载失败: {e}")
        print("尝试直接加载权重...")
        
        # 直接加载权重文件查看结构
        state_dict = paddle.load(PARAMS_FILE)
        print(f"权重文件包含 {len(state_dict)} 个参数")
        print("前5个参数名称:")
        for i, key in enumerate(list(state_dict.keys())[:5]):
            print(f"  {key}: {state_dict[key].shape}")
        
        raise Exception("无法自动构建模型，需要模型定义文件")


def inference_video(video_file):
    """视频推理"""
    if video_file is None:
        return '<div style="padding: 15px; border-radius: 10px; background-color: #fff3e0; border: 2px solid #ff9800"><h3>请上传视频文件</h3></div>'
    
    try:
        print(f"开始处理视频: {video_file}")
        
        # 加载模型
        print("加载模型...")
        model = load_model()
        
        # 预处理
        print("预处理视频...")
        video_data = preprocess_video(video_file, num_seg=1, seg_len=32)
        print(f"预处理完成，数据形状: {video_data.shape}")
        
        # 推理
        print("开始推理...")
        with paddle.no_grad():
            output = model(video_data)
        
        print(f"推理完成，输出形状: {output.shape}")
        
        # 后处理
        output_np = output.numpy()
        pred_class = np.argmax(output_np[0])
        confidence = output_np[0][pred_class]
        
        class_names = ["非暴力行为", "暴力行为"]
        result_class = class_names[pred_class]
        
        print(f"预测结果: {result_class}, 置信度: {confidence:.4f}")
        
        # 返回HTML
        if pred_class == 0:
            return f'''
            <div style="padding: 20px; border-radius: 10px; background-color: #e8f5e9; border: 2px solid #4caf50">
                <h3 style="margin-top: 0; color: #2e7d32">✓ 检测结果：{result_class}</h3>
                <p style="font-size: 1.1em;"><strong>置信度：</strong> {confidence*100:.2f}%</p>
                <p style="color: #558b2f;">该视频未检测到暴力行为</p>
            </div>
            '''
        else:
            return f'''
            <div style="padding: 20px; border-radius: 10px; background-color: #ffebee; border: 2px solid #f44336">
                <h3 style="margin-top: 0; color: #c62828">⚠ 检测结果：{result_class}</h3>
                <p style="font-size: 1.1em;"><strong>置信度：</strong> {confidence*100:.2f}%</p>
                <p style="color: #d32f2f;">警告：该视频包含疑似暴力内容</p>
            </div>
            '''
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"错误: {str(e)}")
        print(error_trace)
        return f'''
        <div style="padding: 15px; border-radius: 10px; background-color: #ffebee; border: 2px solid #ff5252">
            <h3 style="margin-top: 0; color: #c62828">发生错误</h3>
            <p>{str(e)}</p>
            <details><summary>详细信息</summary><pre>{error_trace}</pre></details>
        </div>
        '''


# 创建界面
def create_interface():
    with gr.Blocks() as demo:
        gr.HTML("<h1 style='text-align: center;'>🛡️ 视频暴力行为检测系统</h1>")
        gr.HTML("<p style='text-align: center;'>基于 VideoSwin Transformer (动态图版本)</p>")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 步骤 1: 上传视频")
                video_input = gr.Video(label="选择视频文件")
                submit_btn = gr.Button("开始分析", variant="primary")
                gr.Markdown("""
                ### 说明
                * 支持格式：MP4, AVI等
                * **建议：< 50MB, < 30秒**
                * 分析需要几秒到几十秒
                """)
            
            with gr.Column():
                result_html = gr.HTML("""
                <div style="padding: 20px; border-radius: 10px; background-color: #f5f5f5; border: 2px solid #ddd">
                    <h3>等待分析...</h3>
                    <p>上传视频并点击"开始分析"</p>
                </div>
                """)
        
        submit_btn.click(fn=inference_video, inputs=video_input, outputs=result_html)
    
    return demo


if __name__ == "__main__":
    # 先测试模型加载
    try:
        print("=" * 60)
        print("测试模型加载...")
        print("=" * 60)
        model = load_model()
        print("✓ 模型加载成功！")
        
        # 启动界面
        demo = create_interface()
        demo.launch(
            server_name="0.0.0.0",
            share=True,
            max_file_size="100mb",
            show_error=True
        )
    except Exception as e:
        print(f"✗ 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n请提供模型文件的详细信息以便诊断")
