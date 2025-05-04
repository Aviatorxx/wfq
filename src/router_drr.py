import socket, time, threading, queue, struct, logging, sys
from common import PROJECT_HDR_FMT, PROJECT_HDR_LEN

class DRRRouter:
    def __init__(self):
        self.in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.in_sock.bind(("0.0.0.0", 9000))
        
        self.queues = {}  # flow_id -> queue
        self.quantum = {}  # flow_id -> quantum
        self.deficit = {}  # flow_id -> deficit counter
        self.weights = {}  # flow_id -> weight
        
        # 设置默认权重和量子大小 (增大默认量子值)
        self.default_quantum = 2048  # 默认量子大小 - 增大到足够处理1024字节数据包
        self.default_weight = 1     # 默认权重
        
        # 设置日志
        logging.basicConfig(
            format='[Router] %(message)s',
            level=logging.INFO,
        )
        self.logger = logging.getLogger("DRRRouter")
        
        # 当前活动流索引
        self.active_flows = []
        self.active_flow_index = 0
        
        # 统计信息
        self.packets_received = 0
        self.packets_sent = 0
        self.last_stats_time = time.time()
        
    def set_flow_weight(self, flow_id, weight):
        """设置流的权重"""
        self.weights[flow_id] = weight
        self.quantum[flow_id] = self.default_quantum * weight
        
        # 仅当流不存在时初始化赤字和队列
        if flow_id not in self.queues:
            self.deficit[flow_id] = self.quantum[flow_id]  # 初始赤字设为量子值
            self.queues[flow_id] = queue.Queue()
            self.logger.info(f"创建新流: flow_id={flow_id}, 权重={weight}, 量子={self.quantum[flow_id]}, 初始赤字={self.deficit[flow_id]}")
            
            # 更新活动流列表
            if flow_id not in self.active_flows:
                self.active_flows.append(flow_id)
            
    def enqueue(self, pkt, flow_id):
        """将数据包加入对应流的队列"""
        if flow_id not in self.queues:
            self.set_flow_weight(flow_id, self.default_weight)
        self.queues[flow_id].put(pkt)
        self.packets_received += 1
        
        # 每隔5秒打印一次队列状态
        now = time.time()
        if now - self.last_stats_time > 5:
            self.print_stats()
            self.last_stats_time = now
            
    def print_stats(self):
        """打印路由器状态"""
        queue_lengths = {f: q.qsize() for f, q in self.queues.items()}
        self.logger.info(f"路由器状态: 收到={self.packets_received}, 发送={self.packets_sent}, 队列={queue_lengths}, 活动流={self.active_flows}")
        for flow_id in self.active_flows:
            self.logger.info(f"流 {flow_id}: 权重={self.weights[flow_id]}, 量子={self.quantum[flow_id]}, 赤字={self.deficit[flow_id]}")
        
    def dequeue(self):
        """DRR调度算法"""
        # 获取所有非空队列的流
        self.active_flows = [f for f in self.queues.keys() if not self.queues[f].empty()]
        
        if not self.active_flows:
            return None
            
        # 流的数量可能会动态变化，确保索引有效
        if len(self.active_flows) > 0:
            # 确保索引在有效范围内
            self.active_flow_index = self.active_flow_index % len(self.active_flows)
            flow_id = self.active_flows[self.active_flow_index]
            
            # 始终增加量子值，确保有足够的赤字发送数据包
            self.deficit[flow_id] += self.quantum[flow_id]
            self.logger.info(f"增加赤字: flow_id={flow_id}, 量子值={self.quantum[flow_id]}, 当前赤字={self.deficit[flow_id]}")
                
            # 队列检查（确保队列非空）
            if not self.queues[flow_id].empty():
                # 查看队列头部的包以获取大小
                pkt = self.queues[flow_id].queue[0]
                pkt_size = len(pkt)
                
                if pkt_size <= self.deficit[flow_id]:
                    # 包可以发送，从队列取出
                    pkt = self.queues[flow_id].get()
                    self.deficit[flow_id] -= pkt_size
                    self.logger.info(f"发送数据包: flow_id={flow_id}, 大小={pkt_size}, 剩余赤字={self.deficit[flow_id]}")
                    
                    # 移动到下一个流
                    self.active_flow_index = (self.active_flow_index + 1) % len(self.active_flows)
                    self.packets_sent += 1
                    return pkt
                else:
                    # 包太大，无法发送，移动到下一个流
                    self.logger.info(f"数据包太大: flow_id={flow_id}, 大小={pkt_size}, 赤字={self.deficit[flow_id]}")
                    self.active_flow_index = (self.active_flow_index + 1) % len(self.active_flows)
            else:
                # 队列为空，移动到下一个流
                self.active_flow_index = (self.active_flow_index + 1) % len(self.active_flows)
                
        return None
        
    def recv_loop(self):
        """接收数据包"""
        while True:
            try:
                pkt, addr = self.in_sock.recvfrom(2048)
                # 解析头部，获取flow_id
                header = pkt[:PROJECT_HDR_LEN]
                _, _, _, _, weight, flow_id = struct.unpack(PROJECT_HDR_FMT, header)
                
                # 设置流的权重
                if flow_id not in self.weights or self.weights[flow_id] != weight:
                    self.set_flow_weight(flow_id, weight)
                    
                self.enqueue(pkt, flow_id)
                self.logger.info(f"收到数据包: flow_id={flow_id}, 权重={weight}, 大小={len(pkt)}字节")
            except Exception as e:
                self.logger.error(f"接收数据包出错: {e}")
            
    def send_loop(self):
        """发送数据包"""
        while True:
            pkt = self.dequeue()
            if pkt:
                try:
                    # 解析头部，获取flow_id
                    header = pkt[:PROJECT_HDR_LEN]
                    _, _, _, _, weight, flow_id = struct.unpack(PROJECT_HDR_FMT, header)
                    self.out_sock.sendto(pkt, ("127.0.0.1", 9001))
                    self.logger.info(f"发送数据包: flow_id={flow_id}, 目标=127.0.0.1:9001, 大小={len(pkt)}字节")
                except Exception as e:
                    self.logger.error(f"发送数据包出错: {e}")
            else:
                time.sleep(0.001)  # 避免CPU空转
                
    def run(self):
        """启动路由器"""
        self.logger.info("DRR路由器启动...")
        recv_thread = threading.Thread(target=self.recv_loop)
        send_thread = threading.Thread(target=self.send_loop)
        
        recv_thread.daemon = True
        send_thread.daemon = True
        
        recv_thread.start()
        send_thread.start()
        
        try:
            recv_thread.join()
            send_thread.join()
        except KeyboardInterrupt:
            self.logger.info("路由器正在关闭...")
            sys.exit(0)

if __name__ == "__main__":
    router = DRRRouter()
    router.run() 