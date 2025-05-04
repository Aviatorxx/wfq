import socket, threading, queue, time
import config as C

BUF_SZ = 4096
flow_queues = {}        # flow_id -> queue.Queue
lock = threading.Lock()

# 添加调试输出
print("[Router] 启动中...")


def recv_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", C.ROUTER_PORT_IN))
    print(f"[Router] 接收循环启动，监听端口 {C.ROUTER_PORT_IN}")
    while True:
        data, addr = s.recvfrom(BUF_SZ)
        flow_id = int.from_bytes(data[14:16], "big")   # quick parse
        print(f"[Router] 收到数据包: flow_id={flow_id}, 来自={addr}, 大小={len(data)}字节")
        with lock:
            flow_queues.setdefault(flow_id, queue.Queue()).put(data)

def send_loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[Router] 发送循环启动，目标接收器: {C.RECEIVER_IP}:{C.ROUTER_PORT_OUT}")
    cur = 0
    empty_count = 0
    while True:
        with lock:
            if not flow_queues: 
                time.sleep(0.01)  # 避免CPU空转
                continue
                
            keys = list(flow_queues.keys())
            if not keys:  # 再次检查，以防在获取锁后队列被清空
                time.sleep(0.01)
                continue
                
            # 尝试找到一个非空队列
            found_packet = False
            attempts = 0
            while attempts < len(keys) and not found_packet:
                flow_id = keys[cur % len(keys)]
                cur = (cur + 1) % len(keys)  # 确保不会越界
                
                if not flow_queues[flow_id].empty():
                    pkt = flow_queues[flow_id].get()
                    found_packet = True
                    empty_count = 0  # 重置空计数
                    print(f"[Router] 从队列{flow_id}取出数据包，大小={len(pkt)}字节")
                attempts += 1
                
            if not found_packet:
                empty_count += 1
                if empty_count % 100 == 0:  # 每100次打印一次，避免日志过多
                    print(f"[Router] 所有队列都为空，已尝试{empty_count}次")
                time.sleep(0.01)  # 所有队列都为空，等待一下
                continue
                
            # 如果找到了数据包，就跳出锁的范围发送

        print(f"[Router] 发送数据包: flow_id={flow_id}, 目标={C.RECEIVER_IP}:{C.ROUTER_PORT_OUT}, 大小={len(pkt)}字节")
        s.sendto(pkt, (C.RECEIVER_IP, C.ROUTER_PORT_OUT))

if __name__ == "__main__":
    threading.Thread(target=recv_loop, daemon=True).start()
    send_loop()
