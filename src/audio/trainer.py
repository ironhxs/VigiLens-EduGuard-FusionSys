"""
模型训练模块
"""

import os
import paddle


class AudioTrainer:
    """音频分类模型训练器"""
    
    def __init__(self, model, config):
        """
        初始化训练器
        
        Args:
            model: 模型实例
            config: 配置对象
        """
        self.model = model
        self.config = config
        
        # 损失函数
        self.criterion = paddle.nn.CrossEntropyLoss()
        
        # 优化器
        self.optimizer = paddle.optimizer.Adam(
            learning_rate=config.learning_rate,
            parameters=model.parameters(),
            weight_decay=config.weight_decay
        )
        
        # 学习率调度器
        self.scheduler = paddle.optimizer.lr.ReduceOnPlateau(
            learning_rate=config.learning_rate,
            mode=config.lr_scheduler_mode,
            factor=config.lr_factor,
            patience=config.lr_patience,
            threshold=config.lr_threshold,
            cooldown=config.lr_cooldown,
            min_lr=config.min_lr,
            verbose=True
        )
        
        # 创建模型保存目录
        self.model_dir = config.model_save_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        # 记录最佳准确率
        self.best_val_acc = 0.0
        self.best_epoch = 0
    
    def train_epoch(self, train_loader, epoch):
        """
        训练一个epoch
        
        Args:
            train_loader: 训练数据加载器
            epoch: 当前epoch
            
        Returns:
            tuple: (平均损失, 准确率)
        """
        self.model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (waveforms, labels) in enumerate(train_loader):
            # 添加通道维度
            waveforms = waveforms.unsqueeze(1)
            
            # 前向传播
            logits = self.model(waveforms)
            loss = self.criterion(logits, labels.flatten())
            
            # 反向传播
            loss.backward()
            self.optimizer.step()
            self.optimizer.clear_grad()
            
            # 计算准确率
            preds = paddle.argmax(logits, axis=1)
            train_correct += (preds == labels.flatten()).sum().item()
            train_total += labels.shape[0]
            train_loss += loss.item()
            
            # 定期打印日志
            if batch_idx % self.config.log_interval == 0:
                batch_acc = (preds == labels.flatten()).astype('float32').mean().item()
                print(f"Epoch {epoch + 1}/{self.config.num_epochs}, "
                      f"Batch {batch_idx}/{len(train_loader)}, "
                      f"Loss: {loss.item():.4f}, Acc: {batch_acc:.4f}")
        
        train_acc = train_correct / train_total
        avg_train_loss = train_loss / len(train_loader)
        
        return avg_train_loss, train_acc
    
    def validate(self, val_loader):
        """
        验证模型
        
        Args:
            val_loader: 验证数据加载器
            
        Returns:
            tuple: (平均损失, 准确率)
        """
        self.model.eval()
        val_loss = 0
        val_correct = 0
        val_total = 0
        
        with paddle.no_grad():
            for waveforms, labels in val_loader:
                waveforms = waveforms.unsqueeze(1)
                logits = self.model(waveforms)
                loss = self.criterion(logits, labels.flatten())
                
                preds = paddle.argmax(logits, axis=1)
                val_correct += (preds == labels.flatten()).sum().item()
                val_total += labels.shape[0]
                val_loss += loss.item()
        
        val_acc = val_correct / val_total
        avg_val_loss = val_loss / len(val_loader)
        
        return avg_val_loss, val_acc
    
    def test(self, test_loader):
        """
        测试模型
        
        Args:
            test_loader: 测试数据加载器
            
        Returns:
            float: 测试准确率
        """
        self.model.eval()
        test_correct = 0
        test_total = 0
        
        with paddle.no_grad():
            for waveforms, labels in test_loader:
                waveforms = waveforms.unsqueeze(1)
                logits = self.model(waveforms)
                preds = paddle.argmax(logits, axis=1)
                test_correct += (preds == labels.flatten()).sum().item()
                test_total += labels.shape[0]
        
        test_acc = test_correct / test_total
        return test_acc
    
    def save_checkpoint(self, epoch, val_acc, is_best=False):
        """
        保存模型检查点
        
        Args:
            epoch: 当前epoch
            val_acc: 验证准确率
            is_best: 是否为最佳模型
        """
        # 保存模型参数
        model_path = os.path.join(
            self.model_dir,
            f"model_epoch_{epoch + 1}_acc_{val_acc:.4f}.pdparams"
        )
        paddle.save(self.model.state_dict(), model_path)
        
        if is_best:
            # 保存最佳模型
            best_model_path = os.path.join(self.model_dir, "best_model.pdparams")
            paddle.save(self.model.state_dict(), best_model_path)
            
            # 保存优化器状态
            optim_path = os.path.join(self.model_dir, "best_optimizer.pdopt")
            paddle.save(self.optimizer.state_dict(), optim_path)
            
            print(f"保存新的最佳模型! 验证准确率: {val_acc:.4f}")
    
    def train(self, train_loader, val_loader, test_loader=None):
        """
        完整训练流程
        
        Args:
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            test_loader: 测试数据加载器（可选）
            
        Returns:
            tuple: (最佳验证准确率, 测试准确率)
        """
        print("开始训练...")
        
        for epoch in range(self.config.num_epochs):
            # 训练
            train_loss, train_acc = self.train_epoch(train_loader, epoch)
            
            # 验证
            val_loss, val_acc = self.validate(val_loader)
            
            # 打印epoch结果
            print(f"\nEpoch {epoch + 1}/{self.config.num_epochs} 结果:")
            print(f"训练集 - 损失: {train_loss:.4f}, 准确率: {train_acc:.4f}")
            print(f"验证集 - 损失: {val_loss:.4f}, 准确率: {val_acc:.4f}")
            
            # 更新学习率
            current_lr = self.optimizer.get_lr()
            self.scheduler.step(val_acc)
            new_lr = self.scheduler.get_lr()
            print(f"学习率: {current_lr:.6f} -> {new_lr:.6f}")
            
            # 保存最佳模型
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                self.best_epoch = epoch + 1
                self.save_checkpoint(epoch, val_acc, is_best=True)
            else:
                self.save_checkpoint(epoch, val_acc, is_best=False)
            
            print("-" * 60)
        
        # 训练完成
        print(f"\n训练完成! 最佳模型来自第 {self.best_epoch} 个epoch, "
              f"验证准确率: {self.best_val_acc:.4f}")
        
        # 加载最佳模型进行测试
        if test_loader is not None:
            best_model_path = os.path.join(self.model_dir, "best_model.pdparams")
            if os.path.exists(best_model_path):
                self.model.set_state_dict(paddle.load(best_model_path))
                print(f"加载最佳模型: {best_model_path}")
                
                test_acc = self.test(test_loader)
                print(f"测试集准确率: {test_acc:.4f}")
            else:
                print("警告: 未找到最佳模型文件!")
                test_acc = 0.0
        else:
            test_acc = 0.0
        
        # 保存最终模型
        final_model_path = os.path.join(self.model_dir, "final_model.pdparams")
        paddle.save(self.model.state_dict(), final_model_path)
        print(f"最终模型已保存至: {final_model_path}")
        
        return self.best_val_acc, test_acc
