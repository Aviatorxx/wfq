"""
Router程序 - 实现FIFO和简化WFQ调度算法
支持多流数据包调度和带宽控制
"""

import socket
import time
import threading
import queue
import argparse
import sys
import os
from collections import defaultdict

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from packet_format import ProjectPacket
from utils import RateLimiter, Statistics, Logger

class FlowQueue:
    """每个流的队列"""
    
    def __init__(self, flow_id, weight=1, max_size=1000):
        self.flow_id = flow_id
        self.weight = weight
        self.queue = queue.Queue(maxsize=max_size)
        self.packets_queued = 0
        self.packets_dropped = 0
        self.total_packets = 0
        self.total_bytes = 0
        self.lock = threading.Lock()
        
    def enqueue(self, packet):
        """入队数据包"""
        try:
            self.queue.put_nowait(packet)
            with self.lock:
                self.packets_queued += 1
                self.total_packets += 1
                self.total_bytes += packet.get_size()
            return True
        except queue.Full:
            with self.lock:
                self.packets_dropped += 1
            return False
            
    def dequeue(self):
        """出队数据包"""
        try:
            packet = self.queue.get_nowait()
            with self.lock:
                self.packets_queued -= 1
            return packet
        except queue.Empty:
            return None
            
    def is_empty(self):
        """检查队列是否为空"""
        return self.queue.empty()
        
    def size(self):
        """返回队列大小"""
        return self.queue.qsize()

class UDPRouter:
    """UDP路由器，支持FIFO和WFQ调度"""
    
    def __init__(self, algorithm, bandwidth_kbps, port, receiver_ip, receiver_port):
        self.algorithm = algorithm  # 'fifo' 或 'wfq'
        self.bandwidth = bandwidth_kbps * 1024  # 转换为字节/秒
        self.port = port
        self.receiver_address = (receiver_ip, receiver_port)
        self.running = False
        
        # 创建socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.socket.settimeout(0.1)
        
        # 流队列管理
        self.flow_queues = {}  # flow_id -> FlowQueue
        self.fifo_queue = queue.Queue(maxsize=10000)  # FIFO模式的全局队列
        
        # 带宽控制
        self.rate_limiter = RateLimiter(self.bandwidth)
        
        # WFQ调度状态
        self.current_flow_index = 0
        self.flow_ids = []
        
        # 统计信息
        self.stats = Statistics()
        self.total_received = 0
        self.total_forwarded = 0
        self.total_dropped = 0
        
        # 设置日志
        log_path = f'/Users/aviator/Documents/MCP/wfq/results/router_{algorithm}_{port}.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.logger = Logger.setup_logger(f'router_{algorithm}', log_path)
        
        # 控制线程
        self.receive_thread = None
        self.forward_thread = None
        
    def receive_loop(self):
        """接收循环"""
        self.logger.info(f"Router接收线程启动，算法: {self.algorithm}")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65535)
                recv_time = time.time()
                
                # 解析数据包
                packet = ProjectPacket.unpack(data)
                packet.timestamp = recv_time  # 添加接收时间戳
                
                self.total_received += 1
                
                # 根据调度算法处理
                if self.algorithm == 'fifo':
                    self.handle_fifo_enqueue(packet)
                else:  # wfq
                    self.handle_wfq_enqueue(packet)
                
                # 统计信息
                self.stats.record('packets_received', 1, recv_time,
                                flow_id=packet.flow_id,
                                size=packet.get_size())
                
                if self.total_received % 100 == 0:
                    self.logger.info(f"已接收 {self.total_received} 个数据包")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"接收数据包失败: {e}")
                    
        self.logger.info("接收线程结束")
    
    def handle_fifo_enqueue(self, packet):
        """FIFO入队处理"""
        try:
            self.fifo_queue.put_nowait(packet)
        except queue.Full:
            self.total_dropped += 1
            self.logger.warning(f"FIFO队列已满，丢弃包: Flow {packet.flow_id}")
    
    def handle_wfq_enqueue(self, packet):
        """WFQ入队处理"""
        flow_id = packet.flow_id
        
        # 如果是新流，创建队列
        if flow_id not in self.flow_queues:
            weight = packet.weight
            self.flow_queues[flow_id] = FlowQueue(flow_id, weight)
            self.flow_ids = sorted(self.flow_queues.keys())
            self.logger.info(f"创建新流队列: Flow {flow_id}, 权重={weight}")
        
        # 尝试入队
        flow_queue = self.flow_queues[flow_id]
        if not flow_queue.enqueue(packet):
            self.total_dropped += 1
            self.logger.warning(f"流队列已满，丢弃包: Flow {flow_id}")
    
    def forward_loop(self):
        """转发循环"""
        self.logger.info(f"Router转发线程启动，带宽限制: {self.bandwidth/1024:.1f} KB/s")
        
        while self.running:
            # 根据算法选择下一个要发送的包
            if self.algorithm == 'fifo':
                packet = self.get_next_fifo_packet()
            else:  # wfq
                packet = self.get_next_wfq_packet()
            
            if packet:
                # 重新打包数据包
                packet_data = packet.pack()
                
                # 速率控制
                wait_time = self.rate_limiter.consume(len(packet_data))
                if wait_time > 0:
                    time.sleep(wait_time)
                
                try:
                    # 转发数据包
                    forward_time = time.time()
                    self.socket.sendto(packet_data, self.receiver_address)
                    self.total_forwarded += 1
                    
                    # 计算排队延迟
                    if hasattr(packet, 'timestamp'):
                        queue_delay = (forward_time - packet.timestamp) * 1000
                        
                        self.stats.record('packets_forwarded', 1, forward_time,
                                        flow_id=packet.flow_id,
                                        size=len(packet_data),
                                        queue_delay_ms=queue_delay)
                        
                        if self.total_forwarded % 100 == 0:
                            self.logger.debug(
                                f"转发包: Flow {packet.flow_id}, "
                                f"排队延迟={queue_delay:.2f}ms"
                            )
                    
                except Exception as e:
                    self.logger.error(f"转发数据包失败: {e}")
            else:
                # 没有包可发送，短暂休眠
                time.sleep(0.001)
                
        self.logger.info("转发线程结束")
    
    def get_next_fifo_packet(self):
        """FIFO: 获取下一个要发送的包"""
        try:
            return self.fifo_queue.get_nowait()
        except queue.Empty:
            return None
    
    def get_next_wfq_packet(self):
        """简化WFQ: 使用加权轮询获取下一个要发送的包"""
        if not self.flow_ids:
            return None
        
        # 尝试所有流，找到下一个有包的流
        attempts = 0
        while attempts < len(self.flow_ids):
            # 循环索引
            if self.current_flow_index >= len(self.flow_ids):
                self.current_flow_index = 0
            
            flow_id = self.flow_ids[self.current_flow_index]
            flow_queue = self.flow_queues.get(flow_id)
            
            if flow_queue and not flow_queue.is_empty():
                # 根据权重决定从这个流发送多少包
                weight = flow_queue.weight
                
                # 简化版本：每次只发送一个包，但权重高的流被选中的概率更大
                # 通过重复选择权重次数来实现
                for _ in range(weight):
                    packet = flow_queue.dequeue()
                    if packet:
                        # 下次从下一个流开始
                        self.current_flow_index += 1
                        return packet
            
            # 移动到下一个流
            self.current_flow_index += 1
            attempts += 1
        
        return None
    
    def print_statistics(self):
        """打印统计信息"""
        self.logger.info("=== Router统计 ===")
        self.logger.info(f"接收: {self.total_received} 包")
        self.logger.info(f"转发: {self.total_forwarded} 包")
        self.logger.info(f"丢弃: {self.total_dropped} 包")
        
        if self.total_received > 0:
            drop_rate = self.total_dropped / self.total_received * 100
            self.logger.info(f"丢包率: {drop_rate:.2f}%")
        
        if self.algorithm == 'wfq' and self.flow_queues:
            self.logger.info("\n流队列状态:")
            for flow_id in sorted(self.flow_queues.keys()):
                flow_queue = self.flow_queues[flow_id]
                self.logger.info(
                    f"  Flow {flow_id} (权重={flow_queue.weight}): "
                    f"队列长度={flow_queue.size()}, "
                    f"总包数={flow_queue.total_packets}, "
                    f"丢弃={flow_queue.packets_dropped}"
                )
        
        self.logger.info("==================")
    
    def start(self):
        """启动路由器"""
        self.running = True
        
        # 启动接收和转发线程
        self.receive_thread = threading.Thread(target=self.receive_loop)
        self.forward_thread = threading.Thread(target=self.forward_loop)
        
        self.receive_thread.start()
        self.forward_thread.start()
        
        self.logger.info(f"Router已启动 - 算法: {self.algorithm.upper()}")
        
        # 定期打印统计信息
        try:
            while self.running:
                time.sleep(5)
                self.print_statistics()
        except KeyboardInterrupt:
            pass
    
    def stop(self):
        """停止路由器"""
        self.logger.info("正在停止Router")
        self.running = False
        
        # 等待线程结束
        if self.receive_thread:
            self.receive_thread.join()
        if self.forward_thread:
            self.forward_thread.join()
        
        # 打印最终统计
        self.print_statistics()
        
        # 保存详细统计信息
        summary_path = f'/Users/aviator/Documents/MCP/wfq/results/router_{self.algorithm}_summary.txt'
        with open(summary_path, 'w') as f:
            f.write(f"=== Router Summary ({self.algorithm.upper()}) ===\n")
            f.write(f"Total Received: {self.total_received}\n")
            f.write(f"Total Forwarded: {self.total_forwarded}\n")
            f.write(f"Total Dropped: {self.total_dropped}\n")
            
            if self.total_received > 0:
                drop_rate = self.total_dropped / self.total_received * 100
                forward_rate = self.total_forwarded / self.total_received * 100
                f.write(f"Drop Rate: {drop_rate:.2f}%\n")
                f.write(f"Forward Rate: {forward_rate:.2f}%\n")
            
            if self.algorithm == 'wfq' and self.flow_queues:
                f.write("\nPer-Flow Statistics:\n")
                for flow_id in sorted(self.flow_queues.keys()):
                    fq = self.flow_queues[flow_id]
                    f.write(f"\nFlow {flow_id} (weight={fq.weight}):\n")
                    f.write(f"  Total Packets: {fq.total_packets}\n")
                    f.write(f"  Total Bytes: {fq.total_bytes}\n")
                    f.write(f"  Packets Dropped: {fq.packets_dropped}\n")
                    if fq.total_packets > 0:
                        flow_drop_rate = fq.packets_dropped / fq.total_packets * 100
                        f.write(f"  Drop Rate: {flow_drop_rate:.2f}%\n")
        
        # 关闭socket
        self.socket.close()
        
        self.logger.info("Router已停止")

def main():
    parser = argparse.ArgumentParser(description='Packet Router with FIFO/WFQ')
    parser.add_argument('--algorithm', choices=['fifo', 'wfq'], default='fifo',
                       help='调度算法: fifo 或 wfq')
    parser.add_argument('--bandwidth', type=int, default=1000,
                       help='输出带宽限制（KB/s）')
    parser.add_argument('--port', type=int, default=8080,
                       help='监听端口')
    parser.add_argument('--receiver-ip', default='127.0.0.1',
                       help='Receiver IP地址')
    parser.add_argument('--receiver-port', type=int, default=9090,
                       help='Receiver端口')
    
    args = parser.parse_args()
    
    # 创建并启动路由器
    router = UDPRouter(
        algorithm=args.algorithm,
        bandwidth_kbps=args.bandwidth,
        port=args.port,
        receiver_ip=args.receiver_ip,
        receiver_port=args.receiver_port
    )
    
    try:
        router.start()
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        router.stop()

if __name__ == '__main__':
    main()
