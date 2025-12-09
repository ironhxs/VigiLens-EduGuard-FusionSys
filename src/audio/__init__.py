"""
音频分类模块初始化
"""

from .config import AudioConfig
from .data_preprocessing import AudioPreprocessor
from .dataset import FixedAudioDataset, create_dataloaders
from .model import HTSAT_Swin_Transformer
from .trainer import AudioTrainer
from .inference import AudioClassifier

__all__ = [
    'AudioConfig',
    'AudioPreprocessor', 
    'FixedAudioDataset',
    'create_dataloaders',
    'HTSAT_Swin_Transformer',
    'AudioTrainer',
    'AudioClassifier'
]

__version__ = '1.0.0'
