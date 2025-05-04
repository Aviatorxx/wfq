import socket, threading, queue, time
import config as C

BUF_SZ = 4096
flow_queues = {}        # flow_id -> queue.Queue
flow_weights = {}       # flow_id -> weight
flow_finish_times = {}  # flow_id -> 虚拟完成时间
lock = threading.Lock()

# 添加调试输出
print("[WFQ Router] 启动中...")

def recv_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", C.ROUTER_PORT_IN))
    print(f"[WFQ Router] 接收循环启动，监听端口 {C.ROUTER_PORT_IN}")
    
    while True:
        data, addr = s.recvfrom(BUF_SZ)
        flow_id = int.from_bytes(data[14:16], "big")   # quick parse
        weight = int.from_bytes(data[12:14], "big")    # 获取权重
        
        with lock:
            # 只记录第一个包的权重
            if flow_id not in flow_weights:
                flow_weights[flow_id] = weight
                flow_finish_times[flow_id] = 0  # 初始化虚拟完成时间
            flow_queues.setdefault(flow_id, queue.Queue()).put(data)

def send_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    empty_count = 0
    virtual_time = 0  # 系统虚拟时间
    print(f"[WFQ Router] 发送循环启动，目标接收器: {C.RECEIVER_IP}:{C.ROUTER_PORT_OUT}")
    
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
            
            # 找出下一个要服务的流（虚拟完成时间最小的非空队列）
            min_finish_time = float('inf')
            selected_flow = None
            
            for flow_id in flow_ids:
                if not flow_queues[flow_id].empty():
                    # 如果队列非空且虚拟完成时间小于当前最小值
                    if flow_finish_times[flow_id] < min_finish_time:
                        min_finish_time = flow_finish_times[flow_id]
                        selected_flow = flow_id
            
            if selected_flow is None:
                empty_count += 1
                if empty_count % 100 == 0:  # 每100次打印一次，避免日志过多
                    print(f"[WFQ Router] 所有队列都为空，已尝试{empty_count}次")
                time.sleep(0.01)  # 所有队列都为空，等待一下
                continue
            
            # 取出数据包
            pkt = flow_queues[selected_flow].get()
            size = len(pkt)
            
            # 更新虚拟时间为当前服务流的完成时间
            virtual_time = max(virtual_time, flow_finish_times[selected_flow])
            
            # 计算新的虚拟完成时间
            # 公式: 当前虚拟时间 + 包大小 / 权重
            weight = flow_weights.get(selected_flow, 1)
            flow_finish_times[selected_flow] = virtual_time + size / weight
            
            empty_count = 0  # 重置空计数
            print(f"[WFQ Router] 从队列{selected_flow}(权重:{weight})取出数据包，大小={size}字节，虚拟完成时间={flow_finish_times[selected_flow]:.2f}")

        # 发送数据包
        print(f"[WFQ Router] 发送数据包: flow_id={selected_flow}, 目标={C.RECEIVER_IP}:{C.ROUTER_PORT_OUT}, 大小={len(pkt)}字节")
        s.sendto(pkt, (C.RECEIVER_IP, C.ROUTER_PORT_OUT))

if __name__ == "__main__":
    threading.Thread(target=recv_loop, daemon=True).start()
    send_loop()