"""
HTSAT Swin Transformer模型实现
基于Swin Transformer的音频分类模型
"""

import paddle
import paddle.nn as nn


class ShiftedWindowAttention(nn.Layer):
    """Shifted Window Multi-head Attention"""
    
    def __init__(self, dim, window_size, num_heads, qkv_bias=True, attn_drop=0., proj_drop=0.):
        """
        初始化窗口注意力层
        
        Args:
            dim: 特征维度
            window_size: 窗口大小
            num_heads: 注意力头数
            qkv_bias: 是否使用QKV偏置
            attn_drop: 注意力dropout率
            proj_drop: 投影dropout率
        """
        super().__init__()
        self.dim = dim
        self.window_size = window_size
        self.num_heads = num_heads
        head_dim = dim // num_heads
        self.scale = head_dim ** -0.5
        
        # 线性层
        self.qkv = nn.Linear(dim, dim * 3, bias_attr=qkv_bias)
        self.attn_drop = nn.Dropout(attn_drop)
        self.proj = nn.Linear(dim, dim)
        self.proj_drop = nn.Dropout(proj_drop)
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: 输入特征 [B, L, C]
            
        Returns:
            输出特征 [B, L, C]
        """
        B, L, C = x.shape
        
        # 确保长度可以被窗口大小整除
        pad_len = (self.window_size - L % self.window_size) % self.window_size
        if pad_len > 0:
            x = nn.functional.pad(x, [0, 0, 0, pad_len], data_format="NLC")
            L = L + pad_len
        
        # 重塑为窗口 [B, num_windows, window_size, C]
        x = x.reshape([B, L // self.window_size, self.window_size, C])
        
        # 生成QKV
        qkv = self.qkv(x)
        qkv = qkv.reshape([
            B, L // self.window_size, self.window_size, 
            3, self.num_heads, C // self.num_heads
        ])
        qkv = qkv.transpose([3, 0, 1, 4, 2, 5])
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # 计算注意力
        attn = (q @ k.transpose([0, 1, 2, 4, 3])) * self.scale
        attn = nn.functional.softmax(attn, axis=-1)
        attn = self.attn_drop(attn)
        
        # 输出
        x = attn @ v
        
        # 合并多头输出
        x = x.transpose([0, 1, 3, 2, 4])
        x = x.reshape([B, L // self.window_size, self.window_size, C])
        
        # 投影
        x = self.proj(x)
        x = self.proj_drop(x)
        
        # 恢复原始形状
        x = x.reshape([B, L, C])
        if pad_len > 0:
            x = x[:, :L - pad_len, :]
        
        return x


class HTSAT_Swin_Transformer(nn.Layer):
    """
    HTSAT Swin Transformer音频分类模型
    """
    
    def __init__(self, config):
        """
        初始化模型
        
        Args:
            config: 配置对象
        """
        super().__init__()
        self.config = config
        
        # 频谱图生成层
        self.spectrogram = nn.Sequential(
            nn.Conv1D(
                in_channels=1,
                out_channels=64,
                kernel_size=config.n_fft,
                stride=config.hop_length
            ),
            nn.ReLU(),
            nn.Dropout(config.htsat_drop_rate)
        )
        
        # 线性投影层（将64维特征投影到htsat_dim）
        self.projection = nn.Linear(64, config.htsat_dim)
        
        # Swin Transformer 块
        self.swin_blocks = nn.LayerList([
            self._make_swin_block(
                dim=config.htsat_dim,
                num_heads=config.htsat_num_head,
                window_size=config.htsat_window_size,
                mlp_ratio=config.htsat_mlp_ratio,
                qkv_bias=config.htsat_qkv_bias,
                drop=config.htsat_drop_rate,
                attn_drop=config.htsat_attn_drop_rate
            )
            for _ in range(config.htsat_depth)
        ])
        
        # 分类头
        self.adaptive_pool = nn.AdaptiveAvgPool1D(1)
        self.flatten = nn.Flatten()
        self.classifier = None  # 稍后初始化
    
    def _make_swin_block(self, dim, num_heads, window_size, mlp_ratio=4.,
                         qkv_bias=True, drop=0., attn_drop=0.):
        """创建Swin Transformer块"""
        return nn.Sequential(
            nn.LayerNorm(dim),
            ShiftedWindowAttention(
                dim,
                window_size=window_size,
                num_heads=num_heads,
                qkv_bias=qkv_bias,
                attn_drop=attn_drop,
                proj_drop=drop
            ),
            nn.Linear(dim, dim),
            nn.GELU(),
            nn.Dropout(drop)
        )
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: 输入音频 [batch_size, 1, audio_length]
            
        Returns:
            logits: 分类logits [batch_size, num_classes]
        """
        # 生成频谱图
        x = self.spectrogram(x)  # [batch_size, 64, conv_length]
        
        # 调整维度顺序
        x = x.transpose([0, 2, 1])  # [batch, length, channels]
        
        # 投影到更高维度
        x = self.projection(x)  # [batch_size, conv_length, htsat_dim]
        
        # 通过Swin Transformer块
        for block in self.swin_blocks:
            x = block(x)
        
        # 调整维度顺序
        x = x.transpose([0, 2, 1])  # [batch, channels, length]
        
        # 全局平均池化
        x = self.adaptive_pool(x)  # [batch_size, htsat_dim, 1]
        
        # 展平
        x = self.flatten(x)  # [batch_size, htsat_dim]
        
        # 动态初始化分类头
        if self.classifier is None:
            self.classifier = nn.Linear(x.shape[1], self.config.num_classes)
            print(f"分类头输入维度自动设置为: {x.shape[1]}")
        
        # 分类
        logits = self.classifier(x)
        return logits
    
    def verify_shapes(self, config):
        """
        验证模型各层输入输出形状
        
        Args:
            config: 配置对象
        """
        print("\n=== 模型形状验证 ===")
        
        # 创建测试输入
        test_input = paddle.randn([2, 1, config.audio_length])
        print(f"输入形状: {test_input.shape}")
        
        # 频谱图层
        x = self.spectrogram(test_input)
        print(f"频谱图层输出: {x.shape}")
        
        # 转置和投影
        x = x.transpose([0, 2, 1])
        print(f"转置后: {x.shape}")
        
        x = self.projection(x)
        print(f"投影层输出: {x.shape}")
        
        # Swin块
        for i, block in enumerate(self.swin_blocks):
            x = block(x)
            print(f"Swin块 {i + 1} 输出: {x.shape}")
        
        # 池化和分类
        x = x.transpose([0, 2, 1])
        print(f"池化前转置: {x.shape}")
        
        x = self.adaptive_pool(x)
        print(f"池化层输出: {x.shape}")
        
        x = self.flatten(x)
        print(f"展平层输出: {x.shape}")
        
        # 初始化分类头
        if self.classifier is None:
            self.classifier = nn.Linear(x.shape[1], config.num_classes)
            print(f"分类头输入维度自动设置为: {x.shape[1]}")
        
        x = self.classifier(x)
        print(f"分类层输出: {x.shape}")
        print("==================\n")
