"""
音频数据预处理模块
负责音频数据的加载、预处理和数据集创建
"""

import os
import json
import random
import numpy as np
import pandas as pd
import librosa
from datasets import load_dataset
from tqdm import tqdm


class AudioPreprocessor:
    """音频预处理器"""
    
    def __init__(self, config):
        """
        初始化预处理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.label_map = {0: "non_violence", 1: "violence"}
    
    def preprocess_audio(self, item, is_training=True):
        """
        预处理单个音频样本，确保固定长度
        
        Args:
            item: 数据集中的单个样本
            is_training: 是否为训练模式（影响裁剪策略）
            
        Returns:
            tuple: (音频波形, 标签)
        """
        audio = item['audio']
        y = audio['array']
        
        # 处理空音频
        if len(y) == 0:
            return np.zeros(self.config.audio_length, dtype=np.float32), item['label']
        
        # 处理多声道音频
        if y.ndim > 1:
            y = np.mean(y, axis=0)
        
        # 重采样
        if audio['sampling_rate'] != self.config.sample_rate:
            y = librosa.resample(
                y, 
                orig_sr=audio['sampling_rate'], 
                target_sr=self.config.sample_rate
            )
        
        # 确保音频长度一致
        if len(y) < self.config.audio_length:
            # 短音频填充
            y = np.pad(y, (0, self.config.audio_length - len(y)), mode='constant')
        elif len(y) > self.config.audio_length:
            # 长音频裁剪
            if is_training:
                # 训练时随机裁剪
                start = random.randint(0, len(y) - self.config.audio_length)
            else:
                # 验证/测试时中心裁剪
                start = (len(y) - self.config.audio_length) // 2
            y = y[start:start + self.config.audio_length]
        
        # 最终强制长度匹配（双重保险）
        if len(y) != self.config.audio_length:
            if len(y) > self.config.audio_length:
                y = y[:self.config.audio_length]
            else:
                y = np.pad(y, (0, self.config.audio_length - len(y)), mode='constant')
        
        return y.astype(np.float32), item['label']
    
    def create_processed_dataset(self, dataset, save_path, mode='train'):
        """
        创建并保存预处理后的数据集
        
        Args:
            dataset: HuggingFace数据集
            save_path: 保存路径
            mode: 数据集模式（train/val/test）
            
        Returns:
            DataFrame: 预处理后的数据集
        """
        processed_data = []
        issues = 0
        
        is_training = (mode == 'train')
        
        for i in tqdm(range(len(dataset)), desc=f"处理{mode}集音频样本"):
            try:
                item = dataset[i]
                waveform, label = self.preprocess_audio(item, is_training=is_training)
                
                # 检查长度
                if len(waveform) != self.config.audio_length:
                    issues += 1
                    # 强制修正长度
                    if len(waveform) > self.config.audio_length:
                        waveform = waveform[:self.config.audio_length]
                    else:
                        waveform = np.pad(
                            waveform, 
                            (0, self.config.audio_length - len(waveform)), 
                            mode='constant'
                        )
                
                processed_data.append({
                    "waveform": waveform,
                    "label": label
                })
            except Exception as e:
                print(f"处理样本 {i} 时出错: {str(e)}")
                # 添加静音样本作为后备
                processed_data.append({
                    "waveform": np.zeros(self.config.audio_length, dtype=np.float32),
                    "label": 0
                })
        
        print(f"处理完成! 共 {len(processed_data)} 个样本, {issues} 个样本需要长度修正")
        
        # 保存为Parquet文件
        df = pd.DataFrame(processed_data)
        df.to_parquet(save_path)
        print(f"预处理后的{mode}集已保存至: {save_path}")
        
        return df
    
    def load_and_split_dataset(self, data_file):
        """
        加载并划分数据集
        
        Args:
            data_file: 数据文件路径
            
        Returns:
            tuple: (训练集, 验证集, 测试集)
        """
        print("加载原始数据集...")
        raw_ds = load_dataset('parquet', data_files=data_file)
        full_dataset = raw_ds['train']
        
        # 计算划分大小
        total_size = len(full_dataset)
        train_size = int(self.config.train_ratio * total_size)
        val_size = int(self.config.val_ratio * total_size)
        
        # 划分数据集
        train_dataset = full_dataset.select(range(train_size))
        val_dataset = full_dataset.select(range(train_size, train_size + val_size))
        test_dataset = full_dataset.select(range(train_size + val_size, total_size))
        
        print(f"训练集: {len(train_dataset)} 样本")
        print(f"验证集: {len(val_dataset)} 样本")
        print(f"测试集: {len(test_dataset)} 样本")
        
        return train_dataset, val_dataset, test_dataset
    
    def save_label_map(self, save_dir):
        """保存标签映射"""
        os.makedirs(save_dir, exist_ok=True)
        label_map_path = os.path.join(save_dir, "label_map.json")
        with open(label_map_path, 'w') as f:
            json.dump(self.label_map, f, indent=2)
        print(f"标签映射已保存至: {label_map_path}")
