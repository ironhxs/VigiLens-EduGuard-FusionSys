import os
import sys
import io
import re
import contextlib
from paddle.inference import Config, create_predictor
import gradio as gr
import tempfile
import subprocess  # 用于调用ffmpeg

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# 添加PaddleVideo路径
PADDLEVIDEO_DIR = os.path.join(ROOT_DIR, 'PaddleVideo-develop')
sys.path.append(os.path.join(PADDLEVIDEO_DIR, 'paddlevideo', 'utils'))
sys.path.append(os.path.join(PADDLEVIDEO_DIR, 'tools'))

# 默认路径 - 使用当前目录下的模型
INFERENCE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = None  # 不使用配置文件，直接推理
DEFAULT_MODEL_FILE = os.path.join(INFERENCE_DIR, 'VideoSwin.json')
DEFAULT_PARAMS_FILE = os.path.join(INFERENCE_DIR, 'VideoSwin.pdiparams')

from utils import build_inference_helper
from paddlevideo.utils import get_config

import os
import cv2
import numpy as np
import paddle


def preprocess_video(video_path, num_seg=1, seg_len=32, short_size=256, target_size=224):
    """
    预处理任意视频以满足模型输入要求
    
    Args:
        video_path (str): 视频文件路径
        num_seg (int): 段数，默认为1
        seg_len (int): 每段的帧数，默认为32
        short_size (int): 短边缩放尺寸，默认为256
        target_size (int): 目标裁剪尺寸，默认为224
        
    Returns:
        numpy.ndarray: 预处理后的视频数据，形状为[1, 3, num_seg*seg_len, target_size, target_size]
    """
    # 检查视频文件是否存在
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    
    # 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps if fps > 0 else 0
    
    print(f"视频信息: 总帧数={total_frames}, FPS={fps:.2f}, 时长={duration:.2f}秒")
    
    # 设置要采样的总帧数
    target_frames = num_seg * seg_len
    
    # 计算采样索引
    if total_frames <= 0:
        raise ValueError(f"视频没有有效帧: {video_path}")
    
    # 采样策略
    if total_frames < target_frames:
        # 视频帧数不足，使用循环复制
        print(f"视频帧数不足 ({total_frames} < {target_frames})，将进行循环采样")
        indices = np.arange(total_frames)
        indices = np.tile(indices, int(np.ceil(target_frames / total_frames)))
        indices = indices[:target_frames]
    else:
        # 视频帧数充足，均匀采样
        indices = np.linspace(0, total_frames - 1, target_frames, dtype=int)
    
    # 读取指定索引的帧
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            print(f"警告: 无法读取第 {idx} 帧，将使用黑色帧代替")
            frame = np.zeros((target_size, target_size, 3), dtype=np.uint8)
        frames.append(frame)
    
    # 释放视频捕获
    cap.release()
    
    # 对每一帧进行处理
    processed_frames = []
    for frame in frames:
        # BGR转RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 保持宽高比，将短边缩放到short_size
        height, width = frame.shape[0], frame.shape[1]
        scale = short_size / min(height, width)
        new_height, new_width = int(height * scale), int(width * scale)
        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # 中心裁剪到target_size
        center_h, center_w = new_height // 2, new_width // 2
        half_size = target_size // 2
        frame = frame[
            max(0, center_h - half_size):min(new_height, center_h + half_size),
            max(0, center_w - half_size):min(new_width, center_w + half_size),
            :
        ]
        
        # 处理特殊情况：如果裁剪后尺寸不正确，强制调整大小
        if frame.shape[0] != target_size or frame.shape[1] != target_size:
            frame = cv2.resize(frame, (target_size, target_size), interpolation=cv2.INTER_LINEAR)
        
        # 归一化处理：转换为float32，除以255
        frame = frame.astype(np.float32) / 255.0
        
        # 调整通道顺序：HWC -> CHW (224, 224, 3) -> (3, 224, 224)
        frame = np.transpose(frame, (2, 0, 1))
        
        processed_frames.append(frame)
    
    # 将所有帧合并成一个numpy数组
    video_data = np.stack(processed_frames, axis=0)  # 形状: (32, 3, 224, 224)
    
    # 重新组织形状以符合模型输入要求: (1, 3, 32, 224, 224)
    video_data = np.transpose(video_data, (1, 0, 2, 3))  # 形状: (3, 32, 224, 224)
    video_data = np.expand_dims(video_data, axis=0)  # 形状: (1, 3, 32, 224, 224)
    
    return video_data


def create_paddle_predictor(cfg, model_file, params_file, use_gpu=True, batch_size=1):
    config = Config(model_file, params_file)
    if use_gpu:
        config.enable_use_gpu(8000, 0)
    else:
        config.disable_gpu()
    
    config.switch_ir_optim(True)
    config.enable_memory_optim()
    config.switch_use_feed_fetch_ops(False)
    
    # 计算推理时的真实最大批量大小
    max_batch_size = batch_size
    if 'num_seg' in cfg.INFERENCE:
        num_seg = cfg.INFERENCE.num_seg
        seg_len = cfg.INFERENCE.get('seg_len', 1)
        num_views = 1
        if 'videoswin' in cfg.model_name.lower():
            num_views = 3  # UniformCrop
        max_batch_size = batch_size * num_views * num_seg * seg_len
    
    predictor = create_predictor(config)
    return config, predictor

def check_ffmpeg():
    """检查ffmpeg是否可用"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def convert_webm_to_mp4(input_file):
    """将WebM格式转换为MP4格式"""
    # 检查文件是否为WebM格式
    _, ext = os.path.splitext(input_file.lower())
    if ext != '.webm':
        return input_file  # 不是WebM格式，直接返回原文件
    
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            output_file = temp_file.name
        
        print(f"检测到WebM格式，转换为MP4: {input_file} -> {output_file}")
        
        # 使用ffmpeg进行转换
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-y',
            output_file
        ]
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"转换失败: {result.stderr}")
            # 如果ffmpeg转换失败，尝试使用OpenCV
            return convert_video_with_opencv(input_file)
        
        return output_file
        
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")
        # 尝试使用OpenCV作为备选方案
        return convert_video_with_opencv(input_file)

def convert_video_with_opencv(input_file, output_file=None):
    """使用OpenCV读取视频并保存为MP4格式"""
    if output_file is None:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            output_file = temp_file.name
    
    # 打开输入视频
    cap = cv2.VideoCapture(input_file)
    if not cap.isOpened():
        print(f"无法打开视频: {input_file}")
        return input_file
    
    # 获取视频属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30  # 默认帧率
    
    # 创建视频写入器
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    # 逐帧读取并写入
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    
    # 释放资源
    cap.release()
    out.release()
    
    print(f"已使用OpenCV将视频转换为MP4: {input_file} -> {output_file}")
    return output_file

def inference_video(video_file, config_path=DEFAULT_CONFIG, model_file=DEFAULT_MODEL_FILE, params_file=DEFAULT_PARAMS_FILE):
    """完整的视频推理函数，集成了自定义预处理功能"""
    # 检查视频文件
    if video_file is None:
        return '<div style="padding: 15px; border-radius: 10px; background-color: #fff3e0; border: 2px solid #ff9800"><h3 style="margin-top: 0; color: #e65100">请上传视频文件</h3></div>'
    
    try:
         # 检查文件格式，如果是WebM则转换为MP4
        _, ext = os.path.splitext(video_file.lower())
        if ext == '.webm':
            print(f"检测到WebM格式视频: {video_file}")
            # 检查是否有ffmpeg
            if check_ffmpeg():
                converted_file = convert_webm_to_mp4(video_file)
                if converted_file != video_file:
                    print(f"已将WebM转换为MP4: {video_file} -> {converted_file}")
                    video_file = converted_file
            else:
                print("警告: 检测到WebM格式，但ffmpeg不可用，尝试使用OpenCV转换")
                converted_file = convert_video_with_opencv(video_file)
                if converted_file != video_file:
                    print(f"已使用OpenCV将WebM转换为MP4: {video_file} -> {converted_file}")
                    video_file = converted_file
        # 加载配置
        cfg = get_config(config_path, overrides=[], show=False)
        
        # 初始化推理助手
        inference_helper = build_inference_helper(cfg.INFERENCE)
        
        # 创建预测器
        _, predictor = create_paddle_predictor(cfg, model_file, params_file)
        
        # 获取输入和输出张量
        input_names = predictor.get_input_names()
        output_names = predictor.get_output_names()
        input_tensor_list = []
        output_tensor_list = []
        
        for item in input_names:
            input_tensor_list.append(predictor.get_input_handle(item))
        for item in output_names:
            output_tensor_list.append(predictor.get_output_handle(item))
        
        # 处理视频
        output_text = ""
        try:
            # 首先尝试使用原始方法处理视频
            files = [video_file]
            
            # 捕获控制台输出
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                # 批处理大小为1
                batch_num = 1
                for st_idx in range(0, len(files), batch_num):
                    ed_idx = min(st_idx + batch_num, len(files))
                    
                    # 预处理批处理输入
                    try:
                        batched_inputs = inference_helper.preprocess_batch(files[st_idx:ed_idx])
                        
                        # 运行推理
                        for i in range(len(input_tensor_list)):
                            input_tensor_list[i].copy_from_cpu(batched_inputs[i])
                        predictor.run()
                        
                        batched_outputs = []
                        for j in range(len(output_tensor_list)):
                            batched_outputs.append(output_tensor_list[j].copy_to_cpu())
                        
                        # 调用后处理
                        inference_helper.postprocess(batched_outputs)
                    except Exception as inner_error:
                        print(f"原始预处理失败: {str(inner_error)}")
                        raise inner_error
            
            # 获取捕获的输出
            output_text = f.getvalue()
            
        except Exception as preprocessing_error:
            print(f"原始处理方法失败: {str(preprocessing_error)}，尝试使用自定义预处理...")
            
            try:
                # 获取模型配置参数
                num_seg = cfg.INFERENCE.num_seg
                seg_len = cfg.INFERENCE.seg_len
                short_size = cfg.INFERENCE.get('short_size', 256)
                target_size = cfg.INFERENCE.get('target_size', 224)
                
                # 使用自定义预处理函数
                video_data = preprocess_video(
                    video_file, 
                    num_seg=num_seg, 
                    seg_len=seg_len,
                    short_size=short_size, 
                    target_size=target_size
                )
                
                # 设置输入
                input_tensor_list[0].copy_from_cpu(video_data)
                
                # 运行推理
                predictor.run()
                
                # 获取输出
                batched_outputs = []
                for j in range(len(output_tensor_list)):
                    batched_outputs.append(output_tensor_list[j].copy_to_cpu())
                
                # 捕获输出
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    inference_helper.postprocess(batched_outputs)
                output_text = f.getvalue()
                print("自定义预处理成功，输出:", output_text)
                
            except Exception as custom_error:
                error_trace = traceback.format_exc()
                print(f"自定义预处理失败: {str(custom_error)}\n{error_trace}")
                return f'<div style="padding: 15px; border-radius: 10px; background-color: #ffebee; border: 2px solid #ff5252"><h3 style="margin-top: 0; color: #c62828">处理失败</h3><p>原始方法: {str(preprocessing_error)}</p><p>自定义方法: {str(custom_error)}</p></div>'
        
        # 处理输出结果
        print("最终输出文本:", output_text)
        
        # 使用正则表达式提取结果
        class_pattern = r"top-1 class:\s*(\d+)"
        score_pattern = r"top-1 score:\s*([0-9.]+)"
        
        class_match = re.search(class_pattern, output_text)
        score_match = re.search(score_pattern, output_text)
        
        if class_match and score_match:
            class_id = int(class_match.group(1))
            score = float(score_match.group(1))
            
            # 根据class_id判断是否为暴力行为
            violence_text = "暴力行为" if class_id == 1 else "非暴力行为"
            confidence = score * 100  # 转换为百分比
            
            # 返回结果HTML
            result_html = f"""
            <div style="padding: 15px; border-radius: 10px; background-color: {"#ffebee" if class_id == 1 else "#e8f5e9"}; 
                 border: 2px solid {"#ff5252" if class_id == 1 else "#4caf50"}">
                <h3 style="margin-top: 0; color: {"#d32f2f" if class_id == 1 else "#2e7d32"}">检测结果：{violence_text}</h3>
                <p style="font-size: 16px;">置信度：{confidence:.2f}%</p>
                <div style="background-color: #eee; border-radius: 5px; height: 20px; width: 100%; margin-top: 10px;">
                    <div style="background-color: {"#ff5252" if class_id == 1 else "#4caf50"}; 
                         width: {confidence}%; height: 100%; border-radius: 5px;"></div>
                </div>
            </div>
            """
            return result_html
        else:
            return f'<div style="padding: 15px; border-radius: 10px; background-color: #fff3e0; border: 2px solid #ff9800"><h3 style="margin-top: 0; color: #e65100">无法解析检测结果</h3><p>原始输出: {output_text}</p></div>'
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return f'<div style="padding: 15px; border-radius: 10px; background-color: #ffebee; border: 2px solid #ff5252"><h3 style="margin-top: 0; color: #c62828">发生错误</h3><p>{str(e)}</p><details><summary>详细信息</summary><pre>{error_trace}</pre></details></div>'

# 创建Gradio界面 - 使用更基础的组件
def create_gradio_interface():
    css = """
    .gradio-container {
        background-color: #f9f9f9;
    }
    .header-container {
        background: linear-gradient(90deg, #1976D2, #2196F3);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .footer {
        margin-top: 30px;
        text-align: center;
        color: #666;
    }
    """
    
    with gr.Blocks(css=css, title="视频暴力行为检测系统") as demo:
        # 使用HTML代替Box组件
        gr.HTML("""
        <div class="header-container">
            <h1 style="margin: 0; font-size: 2.2em;">视频暴力行为检测系统</h1>
            <p style="margin-top: 5px; font-size: 1.1em; opacity: 0.9;">基于PaddleVideo VideoSwin模型的视频暴力内容智能识别系统</p>
        </div>
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 步骤 1: 上传视频")
                video_input = gr.Video(label="选择或拖放视频文件")
                
                # size参数在旧版本可能不支持，移除它
                submit_btn = gr.Button("开始分析", variant="primary")
                gr.Markdown("""
                ### 说明
                * 支持常见视频格式：MP4, AVI等
                * 系统将分析视频中是否包含暴力内容
                * 分析可能需要几秒钟时间
                """)
            
            with gr.Column(scale=1):
                # 使用HTML组件来显示结果
                result_html = gr.HTML("""
                <div style="padding: 20px; border-radius: 10px; background-color: #f5f5f5; border: 2px solid #ddd">
                    <h3 style="margin-top: 0;">等待分析...</h3>
                    <p>上传视频并点击"开始分析"按钮</p>
                </div>
                """)
                
                gr.Markdown("### 检测说明")
                gr.Markdown("""
                * **非暴力行为**：视频内容未包含打斗、攻击等暴力场景
                * **暴力行为**：视频包含打斗、攻击或其他形式的暴力行为
                * **置信度**：模型对结果的确信程度，数值越高表示越确信
                """)
        
        gr.Markdown("---")
        gr.HTML('<div class="footer">© 2023 视频暴力行为检测系统 | 基于PaddleVideo</div>')
        
        submit_btn.click(
            fn=inference_video,
            inputs=video_input,
            outputs=result_html
        )
        
    return demo

# 启动Gradio界面
if __name__ == "__main__":
    demo = create_gradio_interface()
    demo.launch(server_name="0.0.0.0", share=True)