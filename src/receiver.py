import socket, argparse, os, sys, time
from common import now_us, log_csv
import config as C

# 添加调试输出
print("[Receiver] 启动中...")

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

def receiver(mode, router_type="fifo"):
    # 统计信息
    packet_counts = {}
    byte_counts = {}
    start_time = time.time()
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((C.RECEIVER_IP, C.ROUTER_PORT_OUT))  # 绑定到路由器输出端口
        print(f"[Receiver] 接收器启动，监听端口 {C.ROUTER_PORT_OUT}，模式: {mode}, 路由器类型: {router_type}")
        
        # 创建一个用于回复的socket
        reply_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 每10秒打印一次统计信息
        last_stats_time = time.time()
        
        while True:
            try:
                data, addr = s.recvfrom(4096)
                ts = now_us()
                flow_id = int.from_bytes(data[14:16], "big")
                size = len(data)
                
                # 更新统计信息
                if flow_id not in packet_counts:
                    packet_counts[flow_id] = 0
                    byte_counts[flow_id] = 0
                packet_counts[flow_id] += 1
                byte_counts[flow_id] += size
                
                # 每100个包只打印一次，减少日志量
                if packet_counts[flow_id] % 100 == 0:
                    print(f"[Receiver] 收到数据包: flow_id={flow_id}, 来自={addr}, 大小={size}字节, 总计: {packet_counts[flow_id]}个包")
                
                # 记录日志
                log_csv(f"logs/recv_log_{router_type}.csv",
                        {"us": ts, "flow": flow_id, "size": size})

                # 定期打印统计信息
                if time.time() - last_stats_time >= 10:
                    print("\n[Receiver] 统计信息:")
                    for flow_id in packet_counts:
                        print(f"  Flow {flow_id}: {packet_counts[flow_id]} 包, {byte_counts[flow_id]} 字节")
                    last_stats_time = time.time()
                
                # 如果是echo模式，发送回复
                if mode == "echo":
                    reply_socket.sendto(data, addr)
                    
            except KeyboardInterrupt:
                print("\n[Receiver] 正在关闭...")
                break
            except Exception as e:
                print(f"[Receiver] 错误: {e}")
                continue
                
    finally:
        s.close()
        if mode == "echo":
            reply_socket.close()
        print("[Receiver] 已关闭")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["log", "echo"], default="log")
    ap.add_argument("--router", choices=["fifo", "rr", "drr"], default="fifo")
    args = ap.parse_args()
    receiver(args.mode, args.router)
