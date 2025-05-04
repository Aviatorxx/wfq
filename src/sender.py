import socket, threading, time, argparse, random, os
from common import make_header, now_us, log_csv
import config as C

# 添加调试输出
print("[Sender] 启动中...")

def udp_sender(flow_id, weight, size, rate_mbps, duration, mode="fifo"):
    """
    连续 duration 秒均匀发包；size 是 UDP payload 总长（含 16B 头）
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sport = C.SENDER_PORT_BASE + flow_id
    s.bind((C.SENDER_BIND_IP, sport))
    print(f"[Sender] 发送器启动: flow_id={flow_id}, weight={weight}, size={size}, rate={rate_mbps}Mbps, 持续={duration}秒, 模式={mode}")

    bits_per_sec = rate_mbps * 1e6
    payload = b'x'*(size-16)        # dummy data
    header  = make_header(b'\x7f\x00\x00\x01',  # 127.0.0.1
                          b'\x7f\x00\x00\x01',
                          sport, C.ROUTER_PORT_IN, weight, flow_id)

    end_t   = time.time() + duration
    seq     = 0
    interval= size*8 / bits_per_sec  # seconds between packets

    while time.time() < end_t:
        send_ts = now_us()
        pkt = header + payload
        print(f"[Sender] 发送数据包: flow_id={flow_id}, 目标={C.ROUTER_IP}:{C.ROUTER_PORT_IN}, 大小={len(pkt)}字节")
        s.sendto(pkt, (C.ROUTER_IP, C.ROUTER_PORT_IN))
        
        # 记录发送的包
        log_csv(f"logs/send_log_{mode}.csv", {
            "us": send_ts, "flow": flow_id,
            "size": len(pkt), "rtt_us": 0})

        # 收回包计算 RTT（非阻塞可用 select/poll）
        try:
            s.settimeout(interval)
            data, addr = s.recvfrom(2048)
            rtt_us = now_us() - send_ts
            print(f"[Sender] 收到回复: flow_id={flow_id}, 来自={addr}, 大小={len(data)}字节, RTT={rtt_us/1000:.2f}ms")
            log_csv(f"logs/send_log_{mode}.csv", {
                "us": send_ts, "flow": flow_id,
                "size": len(data), "rtt_us": rtt_us})
        except socket.timeout:
            pass

        time.sleep(max(0, interval))
        seq += 1

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--flow", type=int, required=True)
    ap.add_argument("--weight", type=int, required=True)
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--rate", type=float, default=1.0)
    ap.add_argument("--dur", type=float, default=10.0)
    ap.add_argument("--mode", choices=["fifo", "rr", "drr"], default="fifo")
    args = ap.parse_args()
    
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    udp_sender(args.flow, args.weight, args.size, args.rate, args.dur, args.mode)
