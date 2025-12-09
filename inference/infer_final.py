#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
最终版推理脚本 - 兼容PIR格式模型
"""

import os
import sys
import cv2
import numpy as np
import gradio as gr
import paddle
import json

INFERENCE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_FILE = os.path.join(INFERENCE_DIR, 'VideoSwin.json')
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
    
    return video_data.astype(np.float32)


def load_pir_model():
    """加载PIR格式的模型"""
    try:
        print("尝试使用jit.load加载PIR模型...")
        # 移除.json后缀
        model_prefix = MODEL_FILE.replace('.json', '')
        model = paddle.jit.load(model_prefix)
        print("✓ PIR模型加载成功！")
        return model
    except Exception as e:
        print(f"jit.load失败: {e}")
        
        # 尝试使用静态图加载
        try:
            print("尝试使用静态图推理...")
            from paddle.static import load_inference_model
            
            exe = paddle.static.Executor(paddle.CPUPlace())
            model_prefix = MODEL_FILE.replace('.json', '')
            
            # 加载模型
            [program, feed_target_names, fetch_targets] = load_inference_model(
                dirname=INFERENCE_DIR,
                executor=exe,
                model_filename=os.path.basename(MODEL_FILE),
                params_filename=os.path.basename(PARAMS_FILE)
            )
            
            print("✓ 静态图模型加载成功！")
            return {
                'exe': exe,
                'program': program,
                'feed_names': feed_target_names,
                'fetch_targets': fetch_targets,
                'type': 'static'
            }
        except Exception as e2:
            print(f"静态图加载也失败: {e2}")
            raise Exception("无法加载模型，请检查模型文件格式")


# 全局模型变量
MODEL = None

def get_model():
    """获取或初始化模型"""
    global MODEL
    if MODEL is None:
        MODEL = load_pir_model()
    return MODEL


def inference_video(video_file):
    """视频推理"""
    if video_file is None:
        return '<div style="padding: 15px; border-radius: 10px; background-color: #fff3e0; border: 2px solid #ff9800"><h3>请上传视频文件</h3></div>'
    
    try:
        print(f"\n{'='*60}")
        print(f"开始处理视频: {video_file}")
        print(f"{'='*60}")
        
        # 加载模型
        model = get_model()
        
        # 预处理
        print("预处理视频...")
        video_data = preprocess_video(video_file, num_seg=1, seg_len=32)
        print(f"✓ 预处理完成，数据形状: {video_data.shape}")
        
        # 推理
        print("开始推理...")
        
        if isinstance(model, dict) and model.get('type') == 'static':
            # 静态图推理
            exe = model['exe']
            program = model['program']
            feed_names = model['feed_names']
            fetch_targets = model['fetch_targets']
            
            results = exe.run(
                program,
                feed={feed_names[0]: video_data},
                fetch_list=fetch_targets
            )
            output = results[0]
        else:
            # 动态图推理
            paddle_tensor = paddle.to_tensor(video_data)
            output = model(paddle_tensor)
            if isinstance(output, paddle.Tensor):
                output = output.numpy()
        
        print(f"✓ 推理完成，输出形状: {output.shape}")
        
        # 后处理
        pred_class = np.argmax(output[0])
        confidence = output[0][pred_class]
        
        class_names = ["非暴力行为", "暴力行为"]
        result_class = class_names[pred_class]
        
        print(f"{'='*60}")
        print(f"预测结果: {result_class}")
        print(f"置信度: {confidence:.4f} ({confidence*100:.2f}%)")
        print(f"{'='*60}\n")
        
        # 返回HTML
        if pred_class == 0:
            return f'''
            <div style="padding: 20px; border-radius: 10px; background-color: #e8f5e9; border: 2px solid #4caf50">
                <h3 style="margin-top: 0; color: #2e7d32">✓ 检测结果：{result_class}</h3>
                <p style="font-size: 1.1em;"><strong>置信度：</strong> {confidence*100:.2f}%</p>
                <div style="background-color: #c8e6c9; border-radius: 5px; height: 20px; margin: 10px 0;">
                    <div style="background-color: #4caf50; height: 100%; border-radius: 5px; width: {confidence*100:.1f}%;"></div>
                </div>
                <p style="color: #558b2f;">该视频未检测到暴力行为</p>
            </div>
            '''
        else:
            return f'''
            <div style="padding: 20px; border-radius: 10px; background-color: #ffebee; border: 2px solid #f44336">
                <h3 style="margin-top: 0; color: #c62828">⚠ 检测结果：{result_class}</h3>
                <p style="font-size: 1.1em;"><strong>置信度：</strong> {confidence*100:.2f}%</p>
                <div style="background-color: #ffcdd2; border-radius: 5px; height: 20px; margin: 10px 0;">
                    <div style="background-color: #f44336; height: 100%; border-radius: 5px; width: {confidence*100:.1f}%;"></div>
                </div>
                <p style="color: #d32f2f;">⚠️ 警告：该视频包含疑似暴力内容</p>
            </div>
            '''
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"\n❌ 错误: {str(e)}")
        print(error_trace)
        return f'''
        <div style="padding: 15px; border-radius: 10px; background-color: #ffebee; border: 2px solid #ff5252">
            <h3 style="margin-top: 0; color: #c62828">❌ 发生错误</h3>
            <p><strong>{str(e)}</strong></p>
            <details><summary>详细信息</summary><pre>{error_trace}</pre></details>
        </div>
        '''


def create_interface():
    """创建Gradio界面"""
    css = """
    .gradio-container {font-family: 'Arial', sans-serif;}
    .header {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
             padding: 30px; border-radius: 15px; margin-bottom: 20px;}
    .header h1 {color: white; margin: 0; font-size: 2.5em;}
    .header p {color: rgba(255,255,255,0.9); margin-top: 10px; font-size: 1.1em;}
    """
    
    with gr.Blocks(css=css) as demo:
        gr.HTML("""
        <div class="header">
            <h1>🛡️ VigiLens 暴力行为检测系统</h1>
            <p>基于 VideoSwin Transformer 的智能视频内容分析</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 步骤 1: 上传视频")
                video_input = gr.Video(label="选择或拖放视频文件")
                submit_btn = gr.Button("🔍 开始分析", variant="primary", size="lg")
                
                gr.Markdown("""
                ### 📋 使用说明
                * **支持格式**: MP4, AVI, MOV 等常见视频格式
                * **建议大小**: < 50MB（上传更快）
                * **建议时长**: < 30秒（分析更快）
                * **处理时间**: 约 10-30 秒
                
                ### ⚙️ 技术信息
                * 模型: VideoSwin Transformer
                * 输入: 32帧 × 224×224
                * 类别: 暴力 / 非暴力
                """)
            
            with gr.Column(scale=1):
                gr.Markdown("### 📊 检测结果")
                result_html = gr.HTML("""
                <div style="padding: 30px; border-radius: 10px; background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                     border: 2px dashed #999; text-align: center;">
                    <h3 style="color: #666;">⏳ 等待分析...</h3>
                    <p style="color: #888;">上传视频并点击"开始分析"按钮</p>
                </div>
                """)
        
        gr.HTML("""
        <div style="text-align: center; margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
            <p style="color: #666; margin: 0;">
                © 2025 VigiLens-EduGuard-FusionSys | 
                <a href="https://github.com/ironhxs/VigiLens-EduGuard-FusionSys" style="color: #667eea;">GitHub</a>
            </p>
        </div>
        """)
        
        submit_btn.click(fn=inference_video, inputs=video_input, outputs=result_html)
    
    return demo


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 启动 VigiLens 暴力行为检测系统")
    print("="*60 + "\n")
    
    # 预加载模型
    try:
        print("📦 预加载模型...")
        get_model()
        print("✓ 模型加载成功，系统就绪！\n")
    except Exception as e:
        print(f"⚠️  模型加载失败: {e}")
        print("系统将在首次推理时尝试加载\n")
    
    # 启动界面
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        max_file_size="100mb",
        show_error=True
    )
