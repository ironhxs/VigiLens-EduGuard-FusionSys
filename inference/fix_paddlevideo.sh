#!/usr/bin/env bash

# 目标文件路径
TARGET_FILE="/home/aistudio/data/PaddleVideo-develop/paddlevideo/loader/pipelines/sample.py"

# 备份原始文件
# cp "$TARGET_FILE" "${TARGET_FILE}.bak"

# 替换 _get_train_clips 方法（修复缩进）
sed -i '/def _get_train_clips(self, num_frames):/,/return clip_offsets/c\
    def _get_train_clips(self, num_frames):\
        # === 动态计算时间跨度和采样间隔 ===\
        ori_seg_len = (self.seg_len - 1) * self.frame_interval + 1 if self.frame_interval else self.seg_len\
        \
        # === 动态调整 seg_len 适配短视频 ===\
        if num_frames < ori_seg_len:\
            self.seg_len = max(1, num_frames // (self.frame_interval + 1) if self.frame_interval else num_frames)\
            ori_seg_len = (self.seg_len - 1) * self.frame_interval + 1 if self.frame_interval else self.seg_len\
        \
        # === 安全计算 avg_interval ===\
        avg_interval = max(1, (num_frames - ori_seg_len) // self.num_seg) if num_frames > ori_seg_len else 0\
        \
        if avg_interval > 0:\
            base_offsets = np.arange(self.num_seg) * avg_interval\
            clip_offsets = np.clip(base_offsets + np.random.randint(avg_interval, size=self.num_seg), 0, num_frames - ori_seg_len)\
        elif num_frames > max(self.num_seg, ori_seg_len):\
            clip_offsets = np.sort(np.random.randint(num_frames - ori_seg_len, size=self.num_seg))\
        else:\
            clip_offsets = np.zeros((self.num_seg,), dtype=np.int)\
        \
        return clip_offsets
' "$TARGET_FILE"

# 替换 _get_test_clips 方法（修复缩进）
sed -i '/def _get_test_clips(self, num_frames):/,/return clip_offsets/c\
    def _get_test_clips(self, num_frames):\
        # === 修正时间跨度计算逻辑 ===\
        ori_seg_len = (self.seg_len - 1) * self.frame_interval + 1 if self.frame_interval else self.seg_len\
        \
        # === 动态调整 seg_len 适配短视频 ===\
        if num_frames < ori_seg_len:\
            self.seg_len = max(1, num_frames // (self.frame_interval + 1) if self.frame_interval else num_frames)\
            ori_seg_len = (self.seg_len - 1) * self.frame_interval + 1 if self.frame_interval else self.seg_len\
        \
        # === 安全计算 avg_interval (避免负数) ===\
        avg_interval = max(0.0, (num_frames - ori_seg_len) / float(self.num_seg)) if num_frames > ori_seg_len else 0.0\
        \
        if avg_interval > 0:\
            base_offsets = np.arange(self.num_seg) * avg_interval\
            max_offset = max(0, num_frames - ori_seg_len)\
            clip_offsets = np.clip((base_offsets + avg_interval / 2.0).astype(np.int), 0, max_offset)\
        else:\
            clip_offsets = np.zeros((self.num_seg, ), dtype=np.int)\
        \
        return clip_offsets
' "$TARGET_FILE"

echo "代码已替换为动态适配版本"

# sed -i 's/dtype=np.int/dtype=int/g' /home/aistudio/data/PaddleVideo-develop/paddlevideo/loader/pipelines/sample.py
find /home/aistudio/data/PaddleVideo-develop/paddlevideo -type f -name '*.py' -exec sed -i 's/\bnp\.int\b/int/g' {} \;
echo "完成 np.int -> int 替换"

# 目标文件路径
# TARGET_FILE="/home/aistudio/data/PaddleVideo-develop/paddlevideo/metrics/center_crop_metric.py"

# 备份原始文件（生成 .bak 备份）
# cp "$TARGET_FILE" "${TARGET_FILE}.bak"

# 替换 self.topk = kwargs.get("topk", [1,5]) → [1]
# sed -i 's/self\.topk\s*=\s*kwargs\.get("topk",\s*\[1,\s*5\])/self.topk = kwargs.get("topk", [1])/g' "$TARGET_FILE"

# 验证替换结果
# echo "修改后的内容（检查是否替换成功）:"
# grep -n 'self.topk = kwargs.get("topk",' "$TARGET_FILE"

# echo "原始文件从top1和5改为仅top1"