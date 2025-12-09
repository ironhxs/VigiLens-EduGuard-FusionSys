"""
音频暴力检测训练主程序
"""

import os
import sys
import argparse
import paddle

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.audio.config import AudioConfig
from src.audio.data_preprocessing import AudioPreprocessor
from src.audio.dataset import create_dataloaders
from src.audio.model import HTSAT_Swin_Transformer
from src.audio.trainer import AudioTrainer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='音频暴力检测模型训练')
    
    # 数据参数
    parser.add_argument('--data_dir', type=str, 
                        default='./audio',
                        help='音频数据目录')
    parser.add_argument('--processed_dir', type=str,
                        default='./processed_audio',
                        help='处理后的数据保存目录')
    
    # 训练参数
    parser.add_argument('--batch_size', type=int, default=16,
                        help='批次大小')
    parser.add_argument('--num_epochs', type=int, default=50,
                        help='训练轮数')
    parser.add_argument('--learning_rate', type=float, default=1e-4,
                        help='学习率')
    parser.add_argument('--weight_decay', type=float, default=1e-5,
                        help='权重衰减')
    
    # 模型参数
    parser.add_argument('--model_save_dir', type=str,
                        default='./saved_audio_models',
                        help='模型保存目录')
    parser.add_argument('--resume', type=str, default=None,
                        help='恢复训练的模型路径')
    
    # 其他参数
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子')
    parser.add_argument('--num_workers', type=int, default=4,
                        help='数据加载线程数')
    parser.add_argument('--use_gpu', action='store_true',
                        help='是否使用GPU')
    
    return parser.parse_args()


def set_seed(seed):
    """设置随机种子"""
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    paddle.seed(seed)


def main():
    """主函数"""
    # 解析参数
    args = parse_args()
    
    # 设置设备
    if args.use_gpu and paddle.is_compiled_with_cuda():
        paddle.set_device('gpu:0')
        print("使用GPU训练")
    else:
        paddle.set_device('cpu')
        print("使用CPU训练")
    
    # 设置随机种子
    set_seed(args.seed)
    print(f"随机种子: {args.seed}")
    
    # 创建配置对象
    config = AudioConfig()
    config.data_dir = args.data_dir
    config.processed_dir = args.processed_dir
    config.batch_size = args.batch_size
    config.num_epochs = args.num_epochs
    config.learning_rate = args.learning_rate
    config.weight_decay = args.weight_decay
    config.model_save_dir = args.model_save_dir
    config.num_workers = args.num_workers
    
    print("\n配置信息:")
    print(f"  数据目录: {config.data_dir}")
    print(f"  批次大小: {config.batch_size}")
    print(f"  训练轮数: {config.num_epochs}")
    print(f"  学习率: {config.learning_rate}")
    print(f"  模型保存目录: {config.model_save_dir}\n")
    
    # 数据预处理
    print("=" * 60)
    print("步骤 1: 数据预处理")
    print("=" * 60)
    
    preprocessor = AudioPreprocessor(config)
    
    # 检查是否已有处理过的数据
    if os.path.exists(config.processed_dir) and len(os.listdir(config.processed_dir)) > 0:
        print(f"发现已处理的数据目录: {config.processed_dir}")
        print("跳过数据预处理步骤")
    else:
        print(f"开始处理音频数据...")
        preprocessor.create_processed_dataset()
        print("数据预处理完成!")
    
    # 加载和划分数据集
    print("\n" + "=" * 60)
    print("步骤 2: 加载数据集")
    print("=" * 60)
    
    train_data, val_data, test_data = preprocessor.load_and_split_dataset()
    print(f"训练集样本数: {len(train_data)}")
    print(f"验证集样本数: {len(val_data)}")
    print(f"测试集样本数: {len(test_data)}")
    
    # 创建数据加载器
    train_loader, val_loader, test_loader = create_dataloaders(
        train_data, val_data, test_data, config
    )
    print(f"训练批次数: {len(train_loader)}")
    print(f"验证批次数: {len(val_loader)}")
    print(f"测试批次数: {len(test_loader)}")
    
    # 创建模型
    print("\n" + "=" * 60)
    print("步骤 3: 创建模型")
    print("=" * 60)
    
    model = HTSAT_Swin_Transformer(config)
    
    # 恢复训练（如果提供了checkpoint）
    if args.resume:
        if os.path.exists(args.resume):
            print(f"加载预训练模型: {args.resume}")
            state_dict = paddle.load(args.resume)
            model.set_state_dict(state_dict)
        else:
            print(f"警告: 未找到模型文件 {args.resume}，从头开始训练")
    
    # 打印模型信息
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if not p.stop_gradient)
    print(f"模型参数总数: {total_params:,}")
    print(f"可训练参数数: {trainable_params:,}")
    
    # 创建训练器
    print("\n" + "=" * 60)
    print("步骤 4: 开始训练")
    print("=" * 60)
    
    trainer = AudioTrainer(model, config)
    
    # 训练模型
    best_val_acc, test_acc = trainer.train(train_loader, val_loader, test_loader)
    
    # 打印最终结果
    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)
    print(f"最佳验证准确率: {best_val_acc:.4f}")
    print(f"测试集准确率: {test_acc:.4f}")
    print(f"模型保存目录: {config.model_save_dir}")


if __name__ == '__main__':
    main()
