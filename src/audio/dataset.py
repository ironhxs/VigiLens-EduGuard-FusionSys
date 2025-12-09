"""
Paddle数据集和数据加载器模块
"""

import numpy as np
import paddle
from paddle.io import Dataset, DataLoader


class FixedAudioDataset(Dataset):
    """
    固定长度音频数据集（用于预处理后的数据）
    """
    
    def __init__(self, dataframe):
        """
        初始化数据集
        
        Args:
            dataframe: 包含预处理后数据的DataFrame
        """
        self.data = dataframe
        print(f"数据集样本数: {len(dataframe)}")
    
    def __getitem__(self, idx):
        """获取单个样本"""
        item = self.data.iloc[idx]
        waveform = paddle.to_tensor(item['waveform'], dtype='float32')
        label = paddle.to_tensor([item['label']], dtype='int64')
        return waveform, label
    
    def __len__(self):
        """数据集大小"""
        return len(self.data)


def create_dataloaders(train_df, val_df, test_df, config):
    """
    创建训练、验证和测试数据加载器
    
    Args:
        train_df: 训练集DataFrame
        val_df: 验证集DataFrame
        test_df: 测试集DataFrame
        config: 配置对象
        
    Returns:
        tuple: (train_loader, val_loader, test_loader)
    """
    # 创建数据集
    train_ds = FixedAudioDataset(train_df)
    val_ds = FixedAudioDataset(val_df)
    test_ds = FixedAudioDataset(test_df)
    
    # 创建数据加载器
    train_loader = DataLoader(
        train_ds,
        batch_size=config.batch_size,
        shuffle=True,
        drop_last=True,
        num_workers=config.num_workers
    )
    
    val_loader = DataLoader(
        val_ds,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers
    )
    
    test_loader = DataLoader(
        test_ds,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers
    )
    
    print(f"训练集批次数量: {len(train_loader)}")
    print(f"验证集批次数量: {len(val_loader)}")
    print(f"测试集批次数量: {len(test_loader)}")
    
    return train_loader, val_loader, test_loader
