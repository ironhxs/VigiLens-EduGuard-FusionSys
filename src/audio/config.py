"""
音频暴力检测配置文件
包含所有训练和模型相关的配置参数
"""


class AudioConfig:
    """音频分类配置类"""
    
    # ============================================================
    # 训练参数
    # ============================================================
    num_epochs = 20              # 训练轮数
    batch_size = 32              # 批次大小
    learning_rate = 0.001        # 初始学习率
    weight_decay = 1e-5          # 权重衰减
    num_workers = 2              # 数据加载线程数
    log_interval = 10            # 日志打印间隔
    
    # ============================================================
    # 音频处理参数
    # ============================================================
    sample_rate = 16000          # 音频采样率
    audio_length = 5 * 16000     # 音频长度（5秒，采样点数）
    
    # ============================================================
    # 频谱图参数
    # ============================================================
    n_fft = 1024                 # FFT窗口大小
    hop_length = 256             # 帧移
    n_mels = 64                  # 梅尔滤波器数量
    
    # ============================================================
    # HTSAT模型参数
    # ============================================================
    htsat_dim = 128              # 特征维度
    htsat_num_head = 4           # 注意力头数
    htsat_window_size = 8        # 窗口大小
    htsat_depth = 4              # Swin Transformer层数
    htsat_mlp_ratio = 4          # MLP扩展比例
    htsat_qkv_bias = True        # 是否使用QKV偏置
    htsat_drop_rate = 0.1        # Dropout率
    htsat_attn_drop_rate = 0.1   # 注意力Dropout率
    
    # ============================================================
    # 分类参数
    # ============================================================
    num_classes = 2              # 类别数（暴力/非暴力）
    
    # ============================================================
    # 路径配置
    # ============================================================
    base_path = "/home/aistudio/data"
    workspace = "audio_workspace"
    dataset_path = "custom_dataset"
    checkpoint_path = "ckpt"
    model_save_dir = "best_models"
    
    # ============================================================
    # 数据集划分比例
    # ============================================================
    train_ratio = 0.8            # 训练集比例
    val_ratio = 0.1              # 验证集比例
    test_ratio = 0.1             # 测试集比例
    
    # ============================================================
    # 学习率调度器参数
    # ============================================================
    lr_scheduler_mode = 'max'    # 监控模式（max表示监控准确率）
    lr_factor = 0.5              # 学习率衰减因子
    lr_patience = 2              # 连续多少epoch没提升时降低学习率
    lr_threshold = 0.001         # 变化阈值
    lr_cooldown = 1              # 冷却期
    min_lr = 1e-6                # 最小学习率
    
    def __repr__(self):
        """打印配置信息"""
        attrs = [attr for attr in dir(self) if not attr.startswith('_') and not callable(getattr(self, attr))]
        config_str = "AudioConfig:\n"
        config_str += "=" * 50 + "\n"
        for attr in attrs:
            config_str += f"  {attr}: {getattr(self, attr)}\n"
        config_str += "=" * 50
        return config_str
