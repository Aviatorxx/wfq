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
                current_time = time.time()
                if current_time - last_stats_time >= 10:
                    elapsed = current_time - start_time
                    print(f"\n[Receiver] 运行时间: {elapsed:.1f}秒, 统计信息:")
                    for fid in sorted(packet_counts.keys()):
                        print(f"  Flow {fid}: {packet_counts[fid]}个包, {byte_counts[fid]/1024:.1f}KB, {byte_counts[fid]/1024/elapsed:.2f}KB/s")
                    last_stats_time = current_time

                if mode == "echo":
                    # 从数据包中提取原始发送者的端口
                    sender_port = int.from_bytes(data[8:10], "big")
                    sender_addr = ("127.0.0.1", sender_port)
                    # 每100个包只打印一次，减少日志量
                    if packet_counts[flow_id] % 100 == 0:
                        print(f"[Receiver] 回复数据包到: {sender_addr}")
                    reply_socket.sendto(data, sender_addr)  # 直接回复给原始发送者
            except socket.error as e:
                print(f"[Receiver] 网络错误: {e}")
                time.sleep(0.1)  # 短暂暂停避免CPU空转
                continue
            except Exception as e:
                print(f"[Receiver] 处理数据包时出错: {e}")
                continue
    except socket.error as e:
        print(f"[Receiver] 无法绑定到端口 {C.ROUTER_PORT_OUT}: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[Receiver] 接收器被用户中断")
        # 打印最终统计信息
        elapsed = time.time() - start_time
        print(f"\n[Receiver] 总运行时间: {elapsed:.1f}秒, 最终统计信息:")
        for fid in sorted(packet_counts.keys()):
            print(f"  Flow {fid}: {packet_counts[fid]}个包, {byte_counts[fid]/1024:.1f}KB, {byte_counts[fid]/1024/elapsed:.2f}KB/s")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["log", "echo"], default="log", help="log: 只记录数据包; echo: 记录并回复数据包")
    parser.add_argument("--router", choices=["fifo", "rr"], default="fifo", help="路由器类型: fifo或rr")
    args = parser.parse_args()
    
    try:
        receiver(args.mode, args.router)
    except KeyboardInterrupt:
        print("\n[Receiver] 接收器被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[Receiver] 发生未预期错误: {e}")
        sys.exit(1)
