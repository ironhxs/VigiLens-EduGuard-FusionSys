"""
音频暴力检测 - 快速示例

这是一个简单的示例,展示如何使用音频模块进行训练和推理。
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

def train_example():
    """训练示例"""
    print("=" * 60)
    print("音频暴力检测模型训练示例")
    print("=" * 60)
    
    from src.audio.config import AudioConfig
    from src.audio.data_preprocessing import AudioPreprocessor
    from src.audio.dataset import create_dataloaders
    from src.audio.model import HTSAT_Swin_Transformer
    from src.audio.trainer import AudioTrainer
    
    # 1. 创建配置
    config = AudioConfig()
    config.data_dir = './audio'
    config.batch_size = 16
    config.num_epochs = 10  # 演示用,实际训练可设置为 50-100
    config.learning_rate = 1e-4
    
    print("\n1. 配置信息:")
    print(f"   数据目录: {config.data_dir}")
    print(f"   批次大小: {config.batch_size}")
    print(f"   训练轮数: {config.num_epochs}")
    
    # 2. 数据预处理
    print("\n2. 数据预处理...")
    preprocessor = AudioPreprocessor(config)
    
    if not os.path.exists(config.processed_dir):
        print("   处理音频数据...")
        preprocessor.create_processed_dataset()
    else:
        print(f"   使用已处理的数据: {config.processed_dir}")
    
    # 3. 加载数据
    print("\n3. 加载数据集...")
    train_data, val_data, test_data = preprocessor.load_and_split_dataset()
    print(f"   训练集: {len(train_data)} 样本")
    print(f"   验证集: {len(val_data)} 样本")
    print(f"   测试集: {len(test_data)} 样本")
    
    # 4. 创建数据加载器
    train_loader, val_loader, test_loader = create_dataloaders(
        train_data, val_data, test_data, config
    )
    
    # 5. 创建模型
    print("\n4. 创建模型...")
    model = HTSAT_Swin_Transformer(config)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   模型参数: {total_params:,}")
    
    # 6. 训练
    print("\n5. 开始训练...")
    trainer = AudioTrainer(model, config)
    best_val_acc, test_acc = trainer.train(train_loader, val_loader, test_loader)
    
    print("\n" + "=" * 60)
    print(f"训练完成!")
    print(f"最佳验证准确率: {best_val_acc:.4f}")
    print(f"测试集准确率: {test_acc:.4f}")
    print("=" * 60)


def inference_example():
    """推理示例"""
    print("=" * 60)
    print("音频暴力检测推理示例")
    print("=" * 60)
    
    from src.audio.inference import AudioClassifier
    from src.audio.config import AudioConfig
    
    # 1. 初始化分类器
    config = AudioConfig()
    model_path = './saved_audio_models/best_model.pdparams'
    
    if not os.path.exists(model_path):
        print(f"\n错误: 未找到模型文件 {model_path}")
        print("请先运行训练示例生成模型")
        return
    
    print("\n1. 加载模型...")
    print(f"   模型路径: {model_path}")
    classifier = AudioClassifier(model_path, config)
    
    # 2. 单个音频预测
    print("\n2. 单个音频预测示例...")
    test_audio = './audio/test_sample.wav'
    
    if os.path.exists(test_audio):
        label, confidence, class_name = classifier.predict(test_audio)
        print(f"   音频: {test_audio}")
        print(f"   预测: {class_name}")
        print(f"   置信度: {confidence:.4f} ({confidence*100:.2f}%)")
    else:
        print(f"   音频文件不存在: {test_audio}")
    
    # 3. 批量预测
    print("\n3. 批量预测示例...")
    audio_dir = './audio/test'
    
    if os.path.exists(audio_dir):
        audio_files = [
            os.path.join(audio_dir, f) 
            for f in os.listdir(audio_dir) 
            if f.endswith('.wav')
        ][:5]  # 只预测前5个
        
        if audio_files:
            results = classifier.predict_batch(audio_files)
            print(f"   处理 {len(results)} 个音频文件:")
            for result in results:
                print(f"   - {os.path.basename(result['path'])}: "
                      f"{result['class_name']} ({result['confidence']:.2%})")
        else:
            print(f"   未找到音频文件")
    else:
        print(f"   目录不存在: {audio_dir}")
    
    print("\n" + "=" * 60)
    print("推理完成!")
    print("=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='音频暴力检测示例')
    parser.add_argument('--mode', type=str, default='train',
                        choices=['train', 'inference'],
                        help='运行模式: train(训练) 或 inference(推理)')
    args = parser.parse_args()
    
    if args.mode == 'train':
        train_example()
    elif args.mode == 'inference':
        inference_example()


if __name__ == '__main__':
    main()
