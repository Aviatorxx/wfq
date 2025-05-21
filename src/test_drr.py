import socket
import struct
import time
import threading
from common import PROJECT_HDR_FMT, PROJECT_HDR_LEN

def create_packet(flow_id, weight, size):
    """创建测试数据包"""
    header = struct.pack(PROJECT_HDR_FMT, 0, 0, 0, 0, weight, flow_id)
    payload = b'x' * (size - PROJECT_HDR_LEN)
    return header + payload

def sender(flow_id, weight, packet_size, interval, duration):
    """发送测试数据包"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    start_time = time.time()
    packets_sent = 0
    
    while time.time() - start_time < duration:
        pkt = create_packet(flow_id, weight, packet_size)
        sock.sendto(pkt, ("127.0.0.1", 9000))
        packets_sent += 1
        time.sleep(interval)
    
    print(f"流 {flow_id} 发送完成: {packets_sent} 个包")
    sock.close()

def main():
    # 测试配置
    flows = [
        (1, 1, 512, 0.001),   # 流1: 权重1, 包大小512字节, 间隔1ms
        (2, 2, 512, 0.001),   # 流2: 权重2, 包大小512字节, 间隔1ms
        (3, 4, 512, 0.001),   # 流3: 权重4, 包大小512字节, 间隔1ms
    ]
    
    # 启动发送线程
    threads = []
    for flow_id, weight, size, interval in flows:
        t = threading.Thread(
            target=sender,
            args=(flow_id, weight, size, interval, 30)  # 运行30秒
        )
        threads.append(t)
        t.start()
    
    # 等待所有发送完成
    for t in threads:
        t.join()

if __name__ == "__main__":
    main() 