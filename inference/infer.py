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
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️ ffmpeg未安装，将使用OpenCV处理视频")
        return False

def convert_video_format(input_file):
    """将各种视频格式转换为MP4格式 (支持WebM, MOV, AVI等)"""
    _, ext = os.path.splitext(input_file.lower())
    supported_formats = ['.webm', '.mov', '.avi', '.mkv', '.flv']
    
    if ext not in supported_formats:
        return input_file  # 已经是标准格式，直接返回
    
    print(f"📹 检测到 {ext.upper()} 格式，开始转换: {input_file}")
    
    # 优先使用OpenCV（不依赖ffmpeg）
    try:
        return convert_video_with_opencv(input_file)
    except Exception as opencv_error:
        print(f"OpenCV转换失败: {opencv_error}")
        
        # 如果OpenCV失败，尝试ffmpeg
        if not check_ffmpeg():
            print("⚠️ ffmpeg不可用且OpenCV转换失败，尝试直接使用WebM文件")
            return input_file  # 直接返回原文件，让后续流程处理
        
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                output_file = temp_file.name
            
            print(f"使用ffmpeg转换: {input_file} -> {output_file}")
            
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"ffmpeg转换失败: {result.stderr}")
                return input_file
            
            return output_file
            
        except Exception as e:
            print(f"ffmpeg转换过程中出错: {str(e)}")
            return input_file

def convert_video_with_opencv(input_file, output_file=None):
    """使用OpenCV读取视频并保存为MP4格式"""
    if output_file is None:
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            output_file = temp_file.name
    
    print(f"🎬 使用OpenCV转换视频: {input_file} -> {output_file}")
    
    # 打开输入视频
    cap = cv2.VideoCapture(input_file)
    if not cap.isOpened():
        print(f"❌ 无法打开视频: {input_file}")
        raise ValueError(f"无法打开视频文件: {input_file}")
    
    # 获取视频属性
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps > 120:
        fps = 30  # 默认帧率
    
    print(f"📊 视频信息: {width}x{height}, {fps:.2f}fps")
    
    # 创建视频写入器 - 尝试多种编码器
    fourcc_list = [
        ('mp4v', cv2.VideoWriter_fourcc(*'mp4v')),
        ('avc1', cv2.VideoWriter_fourcc(*'avc1')),
        ('X264', cv2.VideoWriter_fourcc(*'X264')),
        ('XVID', cv2.VideoWriter_fourcc(*'XVID')),
    ]
    
    out = None
    for codec_name, fourcc in fourcc_list:
        try:
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            if out.isOpened():
                print(f"✅ 使用编码器: {codec_name}")
                break
        except:
            continue
    
    if out is None or not out.isOpened():
        cap.release()
        raise ValueError("无法创建视频写入器，所有编码器都失败")
    
    # 逐帧读取并写入
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frame_count += 1
    
    # 释放资源
    cap.release()
    out.release()
    
    print(f"✅ OpenCV转换完成: 共处理 {frame_count} 帧")
    return output_file

def inference_video(video_file, config_path=DEFAULT_CONFIG, model_file=DEFAULT_MODEL_FILE, params_file=DEFAULT_PARAMS_FILE):
    """完整的视频推理函数，集成了自定义预处理功能"""
    # 检查视频文件
    if video_file is None:
        return '<div style="padding: 15px; border-radius: 10px; background-color: #fff3e0; border: 2px solid #ff9800"><h3 style="margin-top: 0; color: #e65100">请上传视频文件</h3></div>'
    
    # 显示开始处理信息
    print(f"✅ 视频已接收,开始处理: {video_file}")
    print(f"📁 文件大小: {os.path.getsize(video_file) / (1024*1024):.2f} MB")
    
    try:
        # 检查并转换非标准格式视频
        _, ext = os.path.splitext(video_file.lower())
        need_convert = ext in ['.webm', '.mov', '.avi', '.mkv', '.flv']
        
        if need_convert:
            print(f"📹 检测到 {ext.upper()} 格式视频: {video_file}")
            converted_file = convert_video_format(video_file)
            if converted_file != video_file:
                print(f"✅ 视频格式转换成功: {video_file} -> {converted_file}")
                video_file = converted_file
            else:
                print(f"ℹ️ 将直接使用原始文件进行推理")
        
        # 直接使用自定义预处理（不依赖配置文件）
        print("🚀 使用自定义预处理进行推理...")
        
        # 创建预测器配置
        config = Config(model_file, params_file)
        config.enable_use_gpu(100, 0)  # 100MB显存，GPU 0
        config.switch_ir_optim(True)
        predictor = create_predictor(config)
        
        # 获取输入输出
        input_names = predictor.get_input_names()
        output_names = predictor.get_output_names()
        input_handle = predictor.get_input_handle(input_names[0])
        output_handle = predictor.get_output_handle(output_names[0])
        
        # 使用自定义预处理（VideoSwin默认参数）
        video_data = preprocess_video(
            video_file,
            num_seg=1,
            seg_len=32,
            short_size=256,
            target_size=224
        )
        
        # 运行推理
        input_handle.copy_from_cpu(video_data)
        predictor.run()
        output = output_handle.copy_to_cpu()
        
        # 后处理：获取预测结果
        pred_class = np.argmax(output[0])
        confidence = output[0][pred_class]
        
        # 类别映射（0: 非暴力, 1: 暴力）
        class_names = ["非暴力行为", "暴力行为"]
        result_class = class_names[pred_class]
        
        print(f"预测结果: {result_class}, 置信度: {confidence:.4f}")
        
        # 返回格式化的HTML结果
        if pred_class == 0:  # 非暴力
            return f'''
            <div style="padding: 20px; border-radius: 10px; background-color: #e8f5e9; border: 2px solid #4caf50">
                <h3 style="margin-top: 0; color: #2e7d32">✓ 检测结果：{result_class}</h3>
                <p style="font-size: 1.1em;"><strong>置信度：</strong> {confidence*100:.2f}%</p>
                <p style="color: #558b2f;">该视频未检测到暴力行为</p>
            </div>
            '''
        else:  # 暴力
            return f'''
            <div style="padding: 20px; border-radius: 10px; background-color: #ffebee; border: 2px solid #f44336">
                <h3 style="margin-top: 0; color: #c62828">⚠ 检测结果：{result_class}</h3>
                <p style="font-size: 1.1em;"><strong>置信度：</strong> {confidence*100:.2f}%</p>
                <p style="color: #d32f2f;">警告：该视频包含疑似暴力内容</p>
            </div>
            '''
        
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
                gr.Markdown("### 步骤 1: 上传或录制视频")
                video_input = gr.Video(
                    label="选择或拖放视频文件，或使用摄像头录制",
                    sources=["upload", "webcam"],  # 支持上传和录制
                    format="mp4",  # 强制使用mp4格式,比webm小
                    include_audio=False,  # 不包含音频,减小文件大小
                    # 限制文件大小，加快上传速度（单位：字节，这里设为50MB）
                    # 如果需要处理更大视频，增加这个值
                )
                
                # 添加状态提示
                upload_status = gr.Textbox(
                    label="状态",
                    value="等待上传视频...",
                    interactive=False,
                    visible=True
                )
                
                submit_btn = gr.Button("开始分析", variant="primary")
                gr.Markdown("""
                ### 说明
                * 支持视频格式：**MP4, AVI, WebM, MOV**等
                * **支持两种方式**：
                  - 📁 上传已有视频文件(包括iPhone录制的MOV)
                  - 📹 使用摄像头实时录制
                * **录制建议** (AutoDL云服务器):
                  - ⏱️ 录制时长控制在 **5-10秒** (上传更快)
                  - 📦 录制后需上传到云端,请耐心等待
                  - 🌐 上传速度取决于你的网络带宽
                  - ✅ 看到"视频已上传"提示后再点击分析
                * **建议视频大小 < 20MB**
                * **如果预览失败**: 不影响分析,直接点击"开始分析"即可
                * 分析可能需要几秒到十几秒
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
        
        # 视频上传完成后更新状态
        def update_upload_status(video):
            if video is not None:
                return "✅ 视频已上传,点击'开始分析'按钮"
            return "等待上传视频..."
        
        video_input.change(
            fn=update_upload_status,
            inputs=video_input,
            outputs=upload_status
        )
        
        # 点击分析按钮
        submit_btn.click(
            fn=inference_video,
            inputs=video_input,
            outputs=result_html
        )
        
    return demo

# 启动Gradio界面
if __name__ == "__main__":
    demo = create_gradio_interface()
    # AutoDL 云服务器配置
    # share=True: 必须开启,生成公网链接供远程访问
    # max_file_size: 限制50MB,避免上传超时
    demo.launch(
        server_name="0.0.0.0",  # 监听所有网络接口
        server_port=6006,  # AutoDL 常用端口,也可以用其他端口
        share=True,  # 必须为True,生成公网访问链接
        max_file_size="50mb",  # 限制50MB,加快上传速度
        show_error=True,  # 显示详细错误信息
        quiet=True,  # 减少控制台输出
        # 以下参数可选,用于优化
        # inbrowser=False,  # 不自动打开浏览器(云服务器上没浏览器)
    )