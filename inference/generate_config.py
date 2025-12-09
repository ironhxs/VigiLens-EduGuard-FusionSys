import os

def create_config_file(config_dir):
    """创建视频暴力分类的配置文件"""
    os.makedirs(config_dir, exist_ok=True)
    
    config_content = """
    MODEL: #MODEL field
        framework: "RecognizerTransformer" #Mandatory, indicate the type of network, associate to the 'paddlevideo/modeling/framework/' .
        backbone: #Mandatory, indicate the type of backbone, associate to the 'paddlevideo/modeling/backbones/' .
            name: "SwinTransformer3D" #Mandatory, The name of backbone.
            pretrained: "/home/aistudio/data/swin_base_patch4_window7_224.pdparams" #Optional, pretrained model path.
            patch_size: [2, 4, 4]
            embed_dim: 128
            depths: [2, 2, 18, 2]
            num_heads: [4, 8, 16, 32]
            window_size: [8, 7, 7]
            mlp_ratio: 4.
            qkv_bias: True
            qk_scale: None
            drop_rate: 0.0
            attn_drop_rate: 0.0
            drop_path_rate: 0.2
            patch_norm: True
        head:
            name: "I3DHead" #Mandatory, indicate the type of head, associate to the 'paddlevideo/modeling/heads'
            num_classes: 400 #Optional, the number of classes to be classified.
            in_channels: 1024 #input channel of the extracted feature.
            spatial_type: "avg"
            drop_ratio: 0.5 #the ratio of dropout
            std: 0.01 #std value in params initialization
        runtime_cfg: # configuration used when the model is train or test.
            test: # test config
                num_seg: 32
                avg_type: "prob" # 'score' or 'prob'

    DATASET: #DATASET field
        batch_size: 1 #Mandatory, bacth size
        num_workers: 36 #Mandatory, XXX the number of subprocess on each GPU.
        test_batch_size: 1
        train:
            format: "VideoDataset" #Mandatory, indicate the type of dataset, associate to the 'paddlevidel/loader/dateset'
            data_prefix: "" #Mandatory, train data root path
            file_path: "/home/aistudio/data/violence_dataset/list/train_list.txt" #Mandatory, train data index file path
        valid:
            format: "VideoDataset" #Mandatory, indicate the type of dataset, associate to the 'paddlevidel/loader/dateset'
            data_prefix: "" #Mandatory, train data root path
            file_path: "/home/aistudio/data/violence_dataset/list/val_list.txt" #Mandatory, valid data index file path
        test:
            format: "VideoDataset" #Mandatory, indicate the type of dataset, associate to the 'paddlevidel/loader/dateset'
            data_prefix: "" #Mandatory, train data root path
            file_path: "/home/aistudio/data/violence_dataset/list/test_list.txt" #Mandatory, valid data index file path

    PIPELINE: #PIPELINE field TODO.....
        train: #Mandotary, indicate the pipeline to deal with the training data, associate to the 'paddlevideo/loader/pipelines/'
            decode:
                name: "VideoDecoder"
                backend: "decord"
                mode: "train"
            sample:
                name: "Sampler"
                num_seg: 1
                frame_interval: 2
                seg_len: 32
                valid_mode: False
                use_pil: False
            transform: #Mandotary, image transform operator.
                - Scale:
                    short_size: 256
                    fixed_ratio: False
                    keep_ratio: True
                    backend: "cv2"
                    do_round: True
                - RandomResizedCrop:
                    backend: "cv2"
                - Scale:
                    short_size: 224
                    fixed_ratio: False
                    keep_ratio: False
                    backend: "cv2"
                    do_round: True
                - RandomFlip:
                - Normalization:
                    mean: [123.675, 116.28, 103.53]
                    std: [58.395, 57.12, 57.375]
                    tensor_shape: [3, 1, 1, 1]
                    inplace: True
                - Image2Array:
                    data_format: "cthw"
        valid: #Mandatory, indicate the pipeline to deal with the validing data. associate to the 'paddlevideo/loader/pipelines/'
            decode:
                name: "VideoDecoder"
                backend: "decord"
                mode: "valid"
            sample:
                name: "Sampler"
                num_seg: 1
                frame_interval: 2
                seg_len: 32
                valid_mode: True
                use_pil: False
            transform: #Mandotary, image transform operator.
                - Scale:
                    short_size: 256
                    fixed_ratio: False
                    keep_ratio: True
                    backend: "cv2"
                    do_round: True
                - CenterCrop:
                    target_size: 224
                    do_round: False
                    backend: "cv2"
                - Normalization:
                    mean: [123.675, 116.28, 103.53]
                    std: [58.395, 57.12, 57.375]
                    tensor_shape: [3, 1, 1, 1]
                    inplace: True
                - Image2Array:
                    data_format: "cthw"
        test:
            decode:
                name: "VideoDecoder"
                backend: "decord"
                mode: "valid"
            sample:
                name: "Sampler"
                num_seg: 4
                frame_interval: 2
                seg_len: 32
                valid_mode: True
                use_pil: False
            transform: #Mandotary, image transform operator.
                - Scale:
                    short_size: 224
                    fixed_ratio: False
                    keep_ratio: True
                    backend: "cv2"
                    do_round: True
                - UniformCrop:
                    target_size: 224
                    backend: "cv2"
                - Normalization:
                    mean: [123.675, 116.28, 103.53]
                    std: [58.395, 57.12, 57.375]
                    tensor_shape: [3, 1, 1, 1]
                    inplace: True
                - Image2Array:
                    data_format: "cthw"

    OPTIMIZER: #OPTIMIZER field
        name: "AdamW" #Mandatory, the type of optimizer, associate to the 'paddlevideo/solver/'
        beta1: 0.9
        beta2: 0.999
        no_weight_decay_name: "norm relative_position_bias_table"
        learning_rate: #Mandatory, the type of learning rate scheduler, associate to the 'paddlevideo/solver/'
            name: "CustomWarmupCosineStepDecay"
            iter_step: True
            warmup_iters: 2.5
            warmup_ratio: 0.1
            min_lr: 0
            base_lr: 3e-5
            max_epoch: 30
        weight_decay: 0.05

    METRIC:
        name: "CenterCropMetric"

    GRADIENT_ACCUMULATION:
        global_batch_size: 64 # Specify the sum of batches to be calculated by all GPUs

    INFERENCE:
        name: "VideoSwin_Inference_helper"
        num_seg: 1
        seg_len: 32
        short_size: 256
        target_size: 224

    model_name: "VideoSwin"
    log_interval: 20 #Optional, the interal of logger, default:10
    save_interval: 5
    epochs: 30 #Mandatory, total epoch
    log_level: "INFO" #Optional, the logger level. default: "INFO"

"""
    
    config_path = os.path.join(config_dir, 'videoswin_violence.yaml')
    with open(config_path, 'w') as f:
        f.write(config_content)
    return config_path
def main():
    config_dir = "/home/aistudio/data/configs/violence_detection"  # 配置文件目录
    # 创建配置文件
    config_path = create_config_file(config_dir)
    print(f"配置文件创建在: {config_path}")
if __name__ == "__main__":
    main()
