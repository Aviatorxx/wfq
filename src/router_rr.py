import socket, threading, queue, time
import config as C

# 添加调试输出
print("[RR Router] 启动中...")

BUF_SZ = 4096
flow_queues = {}        # flow_id -> queue.Queue
flow_weights = {}       # flow_id -> weight
lock = threading.Lock()

def recv_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", C.ROUTER_PORT_IN))
    while True:
        data, addr = s.recvfrom(BUF_SZ)
        flow_id = int.from_bytes(data[14:16], "big")   # quick parse
        weight = int.from_bytes(data[12:14], "big")    # 获取权重
        
        with lock:
            # 只记录第一个包的权重
            if flow_id not in flow_weights:
                flow_weights[flow_id] = weight
            flow_queues.setdefault(flow_id, queue.Queue()).put(data)

def send_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cur_flow_idx = 0
    empty_count = 0
    print(f"[RR Router] 发送循环启动，目标接收器: {C.RECEIVER_IP}:{C.ROUTER_PORT_OUT}")
    
    # 为每个流维护一个计数器，用于实现加权轮询
    flow_counters = {}  # flow_id -> 剩余发送次数
    
    while True:
        with lock:
            if not flow_queues: 
                time.sleep(0.01)  # 避免CPU空转
                continue
                
            # 获取所有流ID
            flow_ids = list(flow_queues.keys())
            if not flow_ids:
                time.sleep(0.01)  # 避免CPU空转
                continue
            
            # 更新流计数器
            for flow_id in flow_ids:
                if flow_id not in flow_counters:
                    # 初始化计数器为权重值
                    flow_counters[flow_id] = flow_weights.get(flow_id, 1)
            
            # 加权轮询算法 - 考虑权重选择下一个非空队列
            found_packet = False
            attempts = 0
            
            while attempts < len(flow_ids) * 2 and not found_packet:  # 最多尝试两轮
                cur_flow_idx = cur_flow_idx % len(flow_ids)
                flow_id = flow_ids[cur_flow_idx]
                cur_flow_idx += 1
                attempts += 1
                
                # 如果该流还有剩余的发送次数且队列非空
                if flow_counters[flow_id] > 0 and not flow_queues[flow_id].empty():
                    pkt = flow_queues[flow_id].get()
                    flow_counters[flow_id] -= 1  # 减少剩余发送次数
                    
                    # 如果计数器归零，重置为权重值
                    if flow_counters[flow_id] <= 0:
                        flow_counters[flow_id] = flow_weights.get(flow_id, 1)
                        
                    found_packet = True
                    empty_count = 0  # 重置空计数
                    print(f"[RR Router] 从队列{flow_id}(权重:{flow_weights.get(flow_id, 1)})取出数据包，大小={len(pkt)}字节")
                    break
            
            if not found_packet:
                empty_count += 1
                if empty_count % 100 == 0:  # 每100次打印一次，避免日志过多
                    print(f"[RR Router] 所有队列都为空，已尝试{empty_count}次")
                time.sleep(0.01)  # 所有队列都为空，等待一下
                continue

        # 发送数据包
        print(f"[RR Router] 发送数据包: flow_id={flow_id}, 目标={C.RECEIVER_IP}:{C.ROUTER_PORT_OUT}, 大小={len(pkt)}字节")
        s.sendto(pkt, (C.RECEIVER_IP, C.ROUTER_PORT_OUT))

if __name__ == "__main__":
    print("Starting RR (Round Robin) Router...")
    threading.Thread(target=recv_loop, daemon=True).start()
    send_loop()