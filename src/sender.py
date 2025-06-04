"""
Sender程序 - 发送UDP数据包到Router
支持配置流ID、权重、包大小、发送速率等参数
"""

import socket
import time
import threading
import argparse
import sys
import os
import signal
from collections import defaultdict

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from packet_format import ProjectPacket
from utils import RateLimiter, Statistics, Logger

class UDPSender:
    """UDP数据包发送器"""
    
    def __init__(self, flow_id, weight, packet_size, rate_bps, 
                 router_ip, router_port, duration=None, log_file=None):
        self.flow_id = flow_id
        self.weight = weight
        self.packet_size = packet_size
        self.rate_limiter = RateLimiter(rate_bps)
        self.router_address = (router_ip, router_port)
        self.duration = duration
        self.running = False
        
        # 统计信息
        self.stats = Statistics()
        self.seq_num = 0
        self.sent_packets = {}  # 序列号 -> 发送时间
        self.lock = threading.Lock()
        
        # 创建socket
        self.send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recv_socket.bind(('', 0))  # 绑定到任意可用端口
        self.recv_socket.settimeout(0.1)
        self.local_port = self.recv_socket.getsockname()[1]
        self.local_ip = '127.0.0.1'
        
        # 设置日志
        if log_file:
            self.logger = Logger.setup_logger(
                f'sender_flow_{flow_id}', 
                log_file
            )
        else:
            log_path = f'/Users/aviator/Documents/MCP/wfq/results/sender_flow_{flow_id}.log'
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            self.logger = Logger.setup_logger(
                f'sender_flow_{flow_id}',
                log_path
            )
        
        # 创建延迟日志文件
        delay_log_path = f'/Users/aviator/Documents/MCP/wfq/results/experiments/data/delays_flow_{flow_id}.csv'
        os.makedirs(os.path.dirname(delay_log_path), exist_ok=True)
        self.delay_log = open(delay_log_path, 'w')
        self.delay_log.write('timestamp,flow_id,packet_size,sequence_number,delay_ms\n')
        
        # 控制线程
        self.send_thread = None
        self.recv_thread = None
        
    def create_packet(self):
        """创建数据包"""
        # 计算数据负载大小 (减去24字节的项目头)
        data_size = max(0, self.packet_size - 24)
        data = b'X' * data_size
        
        packet = ProjectPacket(
            src_ip=self.local_ip,
            dst_ip=self.router_address[0],
            src_port=self.local_port,
            dst_port=self.router_address[1],
            weight=self.weight,
            flow_id=self.flow_id,
            seq_num=self.seq_num,
            data=data
        )
        
        self.seq_num += 1
        return packet
        
    def send_loop(self):
        """发送循环"""
        self.logger.info(f"开始发送数据包，目标速率: {self.rate_limiter.rate} 字节/秒")
        
        start_time = time.time()
        packets_sent = 0
        
        while self.running:
            if self.duration and (time.time() - start_time) >= self.duration:
                break
                
            # 创建数据包
            packet = self.create_packet()
            packet_data = packet.pack()
            
            # 速率控制
            wait_time = self.rate_limiter.consume(len(packet_data))
            if wait_time > 0:
                time.sleep(wait_time)
            
            try:
                # 发送数据包
                send_time = time.time()
                self.send_socket.sendto(packet_data, self.router_address)
                
                # 记录发送时间
                with self.lock:
                    self.sent_packets[packet.seq_num] = send_time
                
                self.stats.record('packets_sent', 1, send_time, 
                                flow_id=self.flow_id, 
                                seq_num=packet.seq_num,
                                size=len(packet_data))
                
                packets_sent += 1
                
                if packets_sent % 100 == 0:
                    self.logger.info(f"已发送 {packets_sent} 个数据包")
                    
            except Exception as e:
                self.logger.error(f"发送数据包失败: {e}")
                
        self.logger.info(f"发送线程结束，共发送 {packets_sent} 个数据包")
        
    def recv_loop(self):
        """接收循环"""
        self.logger.info("开始接收返回的数据包")
        
        packets_received = 0
        
        while self.running:
            try:
                data, addr = self.recv_socket.recvfrom(65535)
                recv_time = time.time()
                
                # 解析数据包
                packet = ProjectPacket.unpack(data)
                
                # 检查是否是我们发送的包
                if packet.flow_id == self.flow_id:
                    seq_num = packet.seq_num
                    
                    with self.lock:
                        if seq_num in self.sent_packets:
                            # 计算延迟
                            send_time = self.sent_packets[seq_num]
                            delay = (recv_time - send_time) * 1000  # 转换为毫秒
                            
                            # 记录统计信息
                            self.stats.record('packets_received', 1, recv_time,
                                            flow_id=self.flow_id,
                                            seq_num=seq_num,
                                            delay_ms=delay)
                            
                            # 写入延迟日志
                            self.delay_log.write(
                                f"{recv_time},{self.flow_id},{packet.get_size()},{seq_num},{delay:.2f}\n"
                            )
                            self.delay_log.flush()
                            
                            # 删除已确认的包
                            del self.sent_packets[seq_num]
                            packets_received += 1
                            
                            if packets_received % 100 == 0:
                                self.logger.info(f"收到确认: seq={seq_num}, 延迟={delay:.2f}ms")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"接收数据包失败: {e}")
                    
        self.logger.info(f"接收线程结束，收到 {packets_received} 个确认包")
        
    def start(self):
        """启动发送器"""
        self.running = True
        
        # 启动发送和接收线程
        self.send_thread = threading.Thread(target=self.send_loop)
        self.recv_thread = threading.Thread(target=self.recv_loop)
        
        self.send_thread.start()
        self.recv_thread.start()
        
        self.logger.info(f"Sender {self.flow_id} 已启动")
        
    def stop(self):
        """停止发送器"""
        self.logger.info(f"正在停止 Sender {self.flow_id}")
        self.running = False
        
        # 等待线程结束
        if self.send_thread:
            self.send_thread.join()
        if self.recv_thread:
            self.recv_thread.join()
            
        # 打印统计信息
        sent_data = self.stats.get_data('packets_sent')
        recv_data = self.stats.get_data('packets_received')
        
        self.logger.info(f"统计信息: 发送 {len(sent_data)} 包，接收 {len(recv_data)} 包")
        
        if recv_data:
            delays = [item['delay_ms'] for item in recv_data if 'delay_ms' in item]
            if delays:
                avg_delay = sum(delays) / len(delays)
                min_delay = min(delays)
                max_delay = max(delays)
                self.logger.info(f"延迟统计: 平均={avg_delay:.2f}ms, 最小={min_delay:.2f}ms, 最大={max_delay:.2f}ms")
        
        # 关闭资源
        self.send_socket.close()
        self.recv_socket.close()
        self.delay_log.close()
        
        self.logger.info(f"Sender {self.flow_id} 已停止")

def main():
    parser = argparse.ArgumentParser(description='UDP Packet Sender')
    parser.add_argument('--flow-id', type=int, required=True, help='流ID')
    parser.add_argument('--weight', type=int, default=1, help='权重')
    parser.add_argument('--packet-size', type=int, default=1024, help='数据包大小（字节）')
    parser.add_argument('--rate', type=int, default=102400, help='发送速率（字节/秒）')
    parser.add_argument('--router-ip', default='127.0.0.1', help='Router IP地址')
    parser.add_argument('--router-port', type=int, default=8080, help='Router端口')
    parser.add_argument('--duration', type=int, default=30, help='运行时长（秒）')
    parser.add_argument('--log-file', help='日志文件路径')
    
    args = parser.parse_args()
    
    # 创建并启动发送器
    sender = UDPSender(
        flow_id=args.flow_id,
        weight=args.weight,
        packet_size=args.packet_size,
        rate_bps=args.rate,
        router_ip=args.router_ip,
        router_port=args.router_port,
        duration=args.duration,
        log_file=args.log_file
    )
    
    try:
        sender.start()
        
        # 等待指定时长或中断信号
        if args.duration:
            time.sleep(args.duration)
        else:
            while True:
                time.sleep(1)
                
    except KeyboardInterrupt:
        print(f"\n收到中断信号，停止 Sender {args.flow_id}")
    finally:
        sender.stop()

if __name__ == '__main__':
    main()
