"""
Receiver程序 - 接收来自Router的数据包
支持统计模式和回发模式
"""

import socket
import time
import threading
import argparse
import sys
import os
from collections import defaultdict

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from packet_format import ProjectPacket
from utils import Statistics, Logger

class UDPReceiver:
    """UDP数据包接收器"""
    
    def __init__(self, mode, port, log_file='received_data.log'):
        self.mode = mode  # 'stats' 或 'echo'
        self.port = port
        self.log_file = log_file
        self.running = False
        
        # 创建socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('', port))
        self.socket.settimeout(0.1)
        
        # 统计信息 (按流ID分组)
        self.flow_stats = defaultdict(lambda: Statistics())
        self.start_time = None
        
        # 设置日志
        log_path = f'/Users/aviator/Documents/MCP/wfq/results/receiver_{port}.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self.logger = Logger.setup_logger('receiver', log_path)
        
        # 创建数据日志文件
        data_log_path = f'/Users/aviator/Documents/MCP/wfq/results/{log_file}'
        os.makedirs(os.path.dirname(data_log_path), exist_ok=True)
        self.data_log = open(data_log_path, 'w')
        self.data_log.write('timestamp,flow_id,packet_size,sequence_number,delay_ms\n')
        
        # 控制线程
        self.receive_thread = None
        
    def process_packet(self, data, addr, recv_time):
        """处理接收到的数据包"""
        try:
            # 解析数据包
            packet = ProjectPacket.unpack(data)
            flow_id = packet.flow_id
            
            # 记录开始时间
            if self.start_time is None:
                self.start_time = recv_time
                
            # 统计信息
            self.flow_stats[flow_id].record('packets_received', 1, recv_time,
                                          flow_id=flow_id,
                                          seq_num=packet.seq_num,
                                          size=packet.get_size())
            
            # 记录到数据日志文件
            relative_time = recv_time - self.start_time
            self.data_log.write(
                f"{relative_time},{flow_id},{packet.get_size()},{packet.seq_num},0\n"
            )
            self.data_log.flush()
            
            # 如果是echo模式，将数据包发回给发送者
            if self.mode == 'echo':
                # 从包头获取源地址信息
                sender_addr = (packet._int_to_ip(packet.src_ip), packet.src_port)
                self.socket.sendto(data, sender_addr)
                
                if packet.seq_num % 100 == 0:
                    self.logger.debug(f"回发数据包: Flow {flow_id}, seq={packet.seq_num}")
            
            # 定期打印统计信息
            total_packets = sum(len(stats.get_data('packets_received')) 
                              for stats in self.flow_stats.values())
            if total_packets % 100 == 0:
                self.logger.info(f"已接收 {total_packets} 个数据包")
                
        except Exception as e:
            self.logger.error(f"处理数据包失败: {e}")
    
    def receive_loop(self):
        """接收循环"""
        self.logger.info(f"Receiver启动，模式: {self.mode}, 端口: {self.port}")
        
        total_packets = 0
        last_stats_time = time.time()
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65535)
                recv_time = time.time()
                
                # 处理数据包
                self.process_packet(data, addr, recv_time)
                total_packets += 1
                
                # 每5秒打印一次统计信息
                if recv_time - last_stats_time >= 5:
                    self.print_statistics()
                    last_stats_time = recv_time
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"接收错误: {e}")
                    
        self.logger.info(f"接收循环结束，共处理 {total_packets} 个数据包")
    
    def print_statistics(self):
        """打印统计信息"""
        self.logger.info("=== 流量统计 ===")
        
        total_packets = 0
        total_bytes = 0
        
        for flow_id in sorted(self.flow_stats.keys()):
            stats = self.flow_stats[flow_id]
            packets_data = stats.get_data('packets_received')
            
            if packets_data:
                flow_packets = len(packets_data)
                flow_bytes = sum(item['size'] for item in packets_data if 'size' in item)
                
                self.logger.info(
                    f"Flow {flow_id}: {flow_packets} 包, {flow_bytes/1024:.2f} KB"
                )
                
                total_packets += flow_packets
                total_bytes += flow_bytes
        
        self.logger.info(f"总计: {total_packets} 包, {total_bytes/1024:.2f} KB")
        self.logger.info("================")
    
    def start(self):
        """启动接收器"""
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_loop)
        self.receive_thread.start()
        self.logger.info("Receiver已启动")
        
    def stop(self):
        """停止接收器"""
        self.logger.info("正在停止Receiver")
        self.running = False
        
        if self.receive_thread:
            self.receive_thread.join()
            
        # 打印最终统计
        self.print_statistics()
        
        # 保存详细统计信息
        summary_path = '/Users/aviator/Documents/MCP/wfq/results/receiver_summary.txt'
        with open(summary_path, 'w') as f:
            f.write("=== Receiver Summary ===\n")
            f.write(f"Mode: {self.mode}\n")
            f.write(f"Port: {self.port}\n")
            f.write(f"Total Flows: {len(self.flow_stats)}\n")
            f.write("\nFlow Statistics:\n")
            
            total_packets = 0
            total_bytes = 0
            
            for flow_id in sorted(self.flow_stats.keys()):
                stats = self.flow_stats[flow_id]
                packets_data = stats.get_data('packets_received')
                
                if packets_data:
                    flow_packets = len(packets_data)
                    flow_bytes = sum(item['size'] for item in packets_data if 'size' in item)
                    
                    f.write(f"\nFlow {flow_id}:\n")
                    f.write(f"  Packets: {flow_packets}\n")
                    f.write(f"  Bytes: {flow_bytes} ({flow_bytes/1024:.2f} KB)\n")
                    
                    total_packets += flow_packets
                    total_bytes += flow_bytes
                    
            f.write(f"\nTotal:\n")
            f.write(f"  Packets: {total_packets}\n")
            f.write(f"  Bytes: {total_bytes} ({total_bytes/1024:.2f} KB)\n")
        
        # 关闭资源
        self.socket.close()
        self.data_log.close()
        
        self.logger.info("Receiver已停止")

def main():
    parser = argparse.ArgumentParser(description='UDP Packet Receiver')
    parser.add_argument('--mode', choices=['stats', 'echo'], default='stats',
                       help='运行模式: stats(统计) 或 echo(回发)')
    parser.add_argument('--port', type=int, default=9090, help='监听端口')
    parser.add_argument('--log-file', default='received_data.log', 
                       help='数据日志文件名')
    
    args = parser.parse_args()
    
    # 创建并启动接收器
    receiver = UDPReceiver(
        mode=args.mode,
        port=args.port,
        log_file=args.log_file
    )
    
    try:
        receiver.start()
        
        # 保持运行直到收到中断信号
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n收到中断信号")
    finally:
        receiver.stop()

if __name__ == '__main__':
    main()
