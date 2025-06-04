"""
工具函数模块
包含项目中使用的通用工具函数
"""

import time
import threading
import logging
import queue
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import os

# 配置matplotlib字体（适配Mac系统）
plt.rcParams['font.sans-serif'] = ['Songti SC', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

class RateLimiter:
    """速率限制器，使用令牌桶算法"""
    
    def __init__(self, rate_bps):
        """
        初始化速率限制器
        :param rate_bps: 速率（字节/秒）
        """
        self.rate = rate_bps
        self.bucket_size = rate_bps * 2  # 桶大小为2秒的速率
        self.tokens = self.bucket_size
        self.last_update = time.time()
        self.lock = threading.Lock()
        
    def consume(self, bytes_count):
        """
        消费令牌
        :param bytes_count: 需要发送的字节数
        :return: 需要等待的时间
        """
        with self.lock:
            now = time.time()
            # 补充令牌
            elapsed = now - self.last_update
            self.tokens = min(self.bucket_size, 
                            self.tokens + elapsed * self.rate)
            self.last_update = now
            
            if self.tokens >= bytes_count:
                self.tokens -= bytes_count
                return 0  # 无需等待
            else:
                # 计算需要等待的时间
                needed_tokens = bytes_count - self.tokens
                wait_time = needed_tokens / self.rate
                self.tokens = 0
                return wait_time

class Statistics:
    """统计信息收集器"""
    
    def __init__(self):
        self.data = defaultdict(list)
        self.lock = threading.Lock()
        
    def record(self, metric, value, timestamp=None, **kwargs):
        """记录统计数据"""
        if timestamp is None:
            timestamp = time.time()
            
        with self.lock:
            self.data[metric].append({
                'timestamp': timestamp,
                'value': value,
                **kwargs
            })
            
    def get_data(self, metric):
        """获取指定指标的数据"""
        with self.lock:
            return self.data[metric].copy()
            
    def clear(self):
        """清空统计数据"""
        with self.lock:
            self.data.clear()

class Logger:
    """日志工具类"""
    
    @staticmethod
    def setup_logger(name, log_file, level=logging.INFO):
        """设置日志记录器"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        handler = logging.FileHandler(log_file)
        handler.setFormatter(formatter)
        
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(handler)
        
        # 同时输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger

class DataAnalyzer:
    """数据分析和可视化工具"""
    
    @staticmethod
    def plot_throughput_vs_time(data_file, output_file, title="Throughput vs Time"):
        """
        绘制吞吐量随时间变化图
        :param data_file: 数据文件路径
        :param output_file: 输出图片路径  
        :param title: 图表标题
        """
        # 读取数据
        flow_data = defaultdict(list)
        
        with open(data_file, 'r') as f:
            f.readline()  # 跳过标题行
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    timestamp = float(parts[0])
                    flow_id = int(parts[1])
                    packet_size = int(parts[2])
                    flow_data[flow_id].append((timestamp, packet_size))
        
        # 计算累计字节数
        plt.figure(figsize=(12, 8))
        
        for flow_id in sorted(flow_data.keys()):
            timestamps = []
            cumulative_bytes = []
            total_bytes = 0
            
            # 按时间排序
            flow_data[flow_id].sort(key=lambda x: x[0])
            start_time = flow_data[flow_id][0][0] if flow_data[flow_id] else 0
            
            for timestamp, packet_size in flow_data[flow_id]:
                total_bytes += packet_size
                timestamps.append(timestamp - start_time)
                cumulative_bytes.append(total_bytes)
                
            plt.plot(timestamps, cumulative_bytes, 
                    label=f'Flow {flow_id}', linewidth=2, marker='o', markersize=4)
        
        plt.xlabel('时间 (秒)')
        plt.ylabel('累计接收字节数')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
    @staticmethod
    def plot_delay_vs_time(data_file, output_file, title="Packet Delay vs Time"):
        """
        绘制包延迟随时间变化图
        :param data_file: 数据文件路径
        :param output_file: 输出图片路径
        :param title: 图表标题
        """
        flow_data = defaultdict(list)
        
        with open(data_file, 'r') as f:
            f.readline()  # 跳过标题行
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    timestamp = float(parts[0])
                    flow_id = int(parts[1])
                    delay = float(parts[4])
                    flow_data[flow_id].append((timestamp, delay))
        
        plt.figure(figsize=(12, 8))
        
        for flow_id in sorted(flow_data.keys()):
            if not flow_data[flow_id]:
                continue
                
            timestamps = [x[0] for x in flow_data[flow_id]]
            delays = [x[1] for x in flow_data[flow_id]]
            
            # 相对时间
            start_time = min(timestamps)
            timestamps = [t - start_time for t in timestamps]
            
            plt.scatter(timestamps, delays, label=f'Flow {flow_id}', alpha=0.6, s=20)
        
        plt.xlabel('时间 (秒)')
        plt.ylabel('包延迟 (毫秒)')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

def create_test_data(file_path, num_flows=3, packets_per_flow=50):
    """创建测试数据文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        f.write("timestamp,flow_id,packet_size,sequence_number,delay_ms\n")
        
        start_time = time.time()
        for flow_id in range(1, num_flows + 1):
            for seq in range(packets_per_flow):
                timestamp = start_time + seq * 0.1 + flow_id * 0.01
                packet_size = 512 if flow_id == 2 else 1024
                delay = 10 + flow_id * 5 + np.random.normal(0, 2)
                f.write(f"{timestamp},{flow_id},{packet_size},{seq},{delay:.2f}\n")

# 测试代码
if __name__ == "__main__":
    # 测试速率限制器
    print("测试速率限制器...")
    limiter = RateLimiter(1000)  # 1000字节/秒
    
    for i in range(5):
        wait_time = limiter.consume(200)  # 消费200字节
        print(f"发送200字节，需要等待: {wait_time:.3f}秒")
        if wait_time > 0:
            time.sleep(wait_time)
    
    # 测试数据分析
    print("\n测试数据分析...")
    test_file = "/Users/aviator/Documents/MCP/wfq/results/test_data.csv"
    create_test_data(test_file)
    
    DataAnalyzer.plot_throughput_vs_time(
        test_file, 
        "/Users/aviator/Documents/MCP/wfq/results/test_throughput.png",
        "测试吞吐量图"
    )
    
    DataAnalyzer.plot_delay_vs_time(
        test_file,
        "/Users/aviator/Documents/MCP/wfq/results/test_delay.png", 
        "测试延迟图"
    )
    
    print("测试完成！")
