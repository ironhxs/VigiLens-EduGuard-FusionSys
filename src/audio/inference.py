"""
音频分类推理模块
"""

import os
import json
import random
import numpy as np
import librosa
import paddle


class AudioClassifier:
    """音频分类器（用于推理）"""
    
    def __init__(self, model_path, config, label_map_path=None):
        """
        初始化分类器
        
        Args:
            model_path: 模型权重路径
            config: 配置对象
            label_map_path: 标签映射文件路径
        """
        self.config = config
        self.device = paddle.get_device()
        
        # 加载模型（需要导入模型类）
        from .model import HTSAT_Swin_Transformer
        self.model = HTSAT_Swin_Transformer(config)
        state_dict = paddle.load(model_path)
        self.model.set_state_dict(state_dict)
        self.model.eval()
        
        # 加载标签映射
        if label_map_path and os.path.exists(label_map_path):
            with open(label_map_path, 'r') as f:
                self.label_map = json.load(f)
        else:
            self.label_map = {0: "non_violence", 1: "violence"}
        
        print(f"分类器初始化完成，使用模型: {model_path}")
    
    def preprocess_audio(self, audio_path):
        """
        预处理音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            Tensor: 预处理后的音频张量
        """
        # 加载音频
        y, sr = librosa.load(audio_path, sr=self.config.sample_rate, mono=True)
        
        # 确保音频长度一致
        if len(y) < self.config.audio_length:
            # 填充
            y = np.pad(y, (0, self.config.audio_length - len(y)), mode='constant')
        elif len(y) > self.config.audio_length:
            # 中心裁剪（推理时使用确定性裁剪）
            start = (len(y) - self.config.audio_length) // 2
            y = y[start:start + self.config.audio_length]
        
        # 转换为Paddle Tensor
        waveform = paddle.to_tensor(y, dtype='float32').unsqueeze(0).unsqueeze(0)
        
        return waveform
    
    def predict(self, audio_path):
        """
        预测音频类别
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            tuple: (预测标签, 置信度, 标签名称)
        """
        try:
            # 预处理
            waveform = self.preprocess_audio(audio_path)
            
            # 推理
            with paddle.no_grad():
                logits = self.model(waveform)
                probs = paddle.nn.functional.softmax(logits, axis=1).numpy()[0]
                pred_label = np.argmax(probs)
                pred_prob = probs[pred_label]
            
            label_name = self.label_map.get(str(pred_label), f"class_{pred_label}")
            
            return int(pred_label), float(pred_prob), label_name
        
        except Exception as e:
            print(f"处理音频 {audio_path} 时出错: {e}")
            return None, None, None
    
    def predict_batch(self, audio_paths):
        """
        批量预测
        
        Args:
            audio_paths: 音频文件路径列表
            
        Returns:
            list: 预测结果列表
        """
        results = []
        for audio_path in audio_paths:
            result = self.predict(audio_path)
            results.append({
                'path': audio_path,
                'label': result[0],
                'confidence': result[1],
                'class_name': result[2]
            })
        return results
