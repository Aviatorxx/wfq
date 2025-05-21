import socket, time, threading, queue, struct, logging, sys
from common import PROJECT_HDR_FMT, PROJECT_HDR_LEN

# 模拟出口链路带宽（bit/s），实验建议值 5 Mbps
LINK_BPS = 5_000_000

class DRRRouter:
    def __init__(self):
        # 初始化 UDP Socket
        self.in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.in_sock.bind(("0.0.0.0", 9000))

        # DRR 数据结构
        self.queues = {}       # flow_id -> queue.Queue
        self.quantum = {}      # flow_id -> quantum
        self.deficit = {}      # flow_id -> current deficit (bytes)
        self.weights = {}      # flow_id -> configured weight

        # 默认参数
        self.default_quantum = 512     # 基础量子 (与最小包长匹配)
        self.default_weight = 1        # 新流默认权重

        # 日志配置
        logging.basicConfig(format='[Router] %(message)s', level=logging.INFO)
        self.logger = logging.getLogger("DRRRouter")

        # 轮转指针
        self.active_flows = []
        self.active_flow_index = 0

        # 流量统计
        self.packets_received = 0
        self.packets_sent = 0
        self.bytes_received = 0
        self.bytes_sent = 0
        self.flow_stats = {}  # flow_id -> {packets: 0, bytes: 0}
        self.last_stats_time = time.time()

    def set_flow_weight(self, flow_id, weight):
        """为新流或权重变动时设置 quantum 与初始 deficit"""
        self.weights[flow_id] = weight
        self.quantum[flow_id] = self.default_quantum * weight
        # 初始化流队列与赤字
        if flow_id not in self.queues:
            self.queues[flow_id] = queue.Queue()
            self.deficit[flow_id] = 0
            self.logger.info(f"创建新流: id={flow_id}, weight={weight}, quantum={self.quantum[flow_id]}")
            self.active_flows.append(flow_id)

    def enqueue(self, pkt, flow_id):
        """接收并入队"""
        if flow_id not in self.queues:
            self.set_flow_weight(flow_id, self.default_weight)
        self.queues[flow_id].put(pkt)
        self.packets_received += 1
        self.bytes_received += len(pkt)
        
        # 更新流统计
        if flow_id not in self.flow_stats:
            self.flow_stats[flow_id] = {"packets": 0, "bytes": 0}
        self.flow_stats[flow_id]["packets"] += 1
        self.flow_stats[flow_id]["bytes"] += len(pkt)
        
        # 间隔 5 秒打印状态
        now = time.time()
        if now - self.last_stats_time > 5:
            self.print_stats()
            self.last_stats_time = now

    def print_stats(self):
        """输出当前队列与赤字状态"""
        lengths = {fid: q.qsize() for fid, q in self.queues.items()}
        self.logger.info(f"总统计: 接收包数={self.packets_received}, 发送包数={self.packets_sent}")
        self.logger.info(f"总统计: 接收字节={self.bytes_received}, 发送字节={self.bytes_sent}")
        self.logger.info(f"队列长度: {lengths}")
        
        for fid in self.active_flows:
            stats = self.flow_stats.get(fid, {"packets": 0, "bytes": 0})
            self.logger.info(f"流 {fid}: weight={self.weights[fid]}, quantum={self.quantum[fid]}, "
                           f"deficit={self.deficit[fid]}, 处理包数={stats['packets']}, "
                           f"处理字节={stats['bytes']}")

    def dequeue(self):
        """DRR 调度：本轮为流累加量子，并在同一轮中连续发包"""
        # 筛选所有非空流
        self.active_flows = [fid for fid, q in self.queues.items() if not q.empty()]
        if not self.active_flows:
            return None

        # 保持索引合法
        self.active_flow_index %= len(self.active_flows)
        fid = self.active_flows[self.active_flow_index]

        # 本轮累加量子，但确保赤字不超过量子值
        if self.deficit[fid] < self.quantum[fid]:
            self.deficit[fid] += self.quantum[fid]
            self.logger.info(f"调度流 {fid}: 累加量子 {self.quantum[fid]}, 当前赤字 {self.deficit[fid]}")
        else:
            # 如果赤字已经达到或超过量子值，重置为0
            self.deficit[fid] = 0
            self.logger.info(f"流 {fid} 赤字达到量子值，重置为0")

        q = self.queues[fid]
        # 连续发送：只要队头包大小 <= 赤字，就出队并返回
        while not q.empty():
            pkt = q.queue[0]                  # peek
            size = len(pkt)
            if size <= self.deficit[fid]:
                q.get()
                self.deficit[fid] -= size
                self.packets_sent += 1
                self.bytes_sent += size
                self.logger.info(f"流 {fid} 发送包: 大小={size}, 剩余赤字={self.deficit[fid]}")
                return pkt
            break

        # 赤字不足或队列空，切换到下一个流
        self.active_flow_index = (self.active_flow_index + 1) % len(self.active_flows)
        self.logger.info(f"流 {fid} 赤字不足或队列空，切换到下一个流")
        return None

    def recv_loop(self):
        """持续接收来自 Sender 的 UDP 包"""
        while True:
            pkt, addr = self.in_sock.recvfrom(2048)
            header = pkt[:PROJECT_HDR_LEN]
            _, _, _, _, weight, flow_id = struct.unpack(PROJECT_HDR_FMT, header)
            # 更新权重 & 初始化队列
            if flow_id not in self.weights or self.weights[flow_id] != weight:
                self.set_flow_weight(flow_id, weight)
            # 入队
            self.enqueue(pkt, flow_id)

    def send_loop(self):
        """持续调度并转发到 Receiver"""
        while True:
            pkt = self.dequeue()
            if pkt is None:
                time.sleep(0.0005)
                continue
            # 转发并限速
            self.out_sock.sendto(pkt, ("127.0.0.1", 9001))
            time.sleep(len(pkt) * 8 / LINK_BPS)

    def run(self):
        """启动接收与发送线程"""
        self.logger.info("DRR Router 启动")
        t1 = threading.Thread(target=self.recv_loop, daemon=True)
        t2 = threading.Thread(target=self.send_loop, daemon=True)
        t1.start(); t2.start()
        try:
            t1.join()
            t2.join()
        except KeyboardInterrupt:
            self.logger.info("路由器关闭中...")
            sys.exit(0)

if __name__ == "__main__":
    DRRRouter().run()
