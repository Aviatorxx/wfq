# 网络调度算法对比系统设计报告

## 1. 项目概述

### 1.1 项目目标
本项目旨在实现一个网络数据包调度算法对比系统，通过实际的UDP网络通信来比较FIFO（先进先出）和WFQ（加权公平队列）两种调度算法的性能差异。

### 1.2 系统架构
系统采用三层架构设计：
- **应用层**: Sender程序生成网络流量
- **网络层**: Router程序实现调度算法
- **接收层**: Receiver程序统计和分析数据

```
┌─────────────┐    UDP     ┌─────────────┐    UDP     ┌─────────────┐
│   Sender    │ ──────────→│   Router    │ ──────────→│  Receiver   │
│ (多个流)     │            │ (调度算法)   │            │ (统计分析)   │
└─────────────┘            └─────────────┘            └─────────────┘
```

## 2. 技术设计

### 2.1 数据包格式设计

#### 项目头结构（24字节）
```c
struct ProjectHeader {
    uint32_t src_ip;        // 源IP地址 (4字节)
    uint32_t dst_ip;        // 目标IP地址 (4字节)
    uint16_t src_port;      // 源端口 (2字节)
    uint16_t dst_port;      // 目标端口 (2字节)
    uint32_t weight;        // 流权重 (4字节)
    uint32_t flow_id;       // 流标识 (4字节)
    uint32_t seq_num;       // 序列号 (4字节)
};
```

#### 设计考虑
- **网络字节序**: 使用大端序确保跨平台兼容
- **固定头长度**: 24字节头便于解析和处理
- **扩展性**: 权重和流ID字段支持复杂调度需求

### 2.2 核心组件设计

#### 2.2.1 Sender组件
**主要功能**:
- 生成指定速率的UDP数据包
- 支持多流并发发送
- 计算端到端延迟

**关键技术**:
```python
class UDPSender:
    def __init__(self, flow_id, weight, packet_size, rate_bps, ...):
        self.rate_limiter = RateLimiter(rate_bps)  # 令牌桶速率控制
        self.sent_packets = {}  # 序列号 -> 发送时间映射
        
    def send_loop(self):
        while self.running:
            packet = self.create_packet()
            wait_time = self.rate_limiter.consume(len(packet))
            if wait_time > 0:
                time.sleep(wait_time)
            self.socket.sendto(packet, router_address)
```

**速率控制算法**:
采用令牌桶算法实现精确的速率控制：
- 令牌以恒定速率生成
- 发送数据包需要消费对应数量的令牌
- 当令牌不足时需要等待

#### 2.2.2 Router组件
**主要功能**:
- 实现FIFO和WFQ调度算法
- 提供带宽限制和队列管理
- 转发数据包到接收器

**FIFO调度实现**:
```python
def handle_fifo_enqueue(self, packet):
    try:
        self.fifo_queue.put_nowait(packet)
    except queue.Full:
        self.total_dropped += 1  # 队列满时丢包

def get_next_fifo_packet(self):
    try:
        return self.fifo_queue.get_nowait()
    except queue.Empty:
        return None
```

**简化WFQ调度实现**:
```python
def handle_wfq_enqueue(self, packet):
    flow_id = packet.flow_id
    if flow_id not in self.flow_queues:
        weight = packet.weight
        self.flow_queues[flow_id] = FlowQueue(flow_id, weight)
    
    self.flow_queues[flow_id].enqueue(packet)

def get_next_wfq_packet(self):
    # 加权轮询调度
    for _ in range(len(self.flow_ids)):
        flow_id = self.flow_ids[self.current_flow_index]
        flow_queue = self.flow_queues[flow_id]
        
        if not flow_queue.is_empty():
            # 根据权重发送多个包
            for _ in range(flow_queue.weight):
                packet = flow_queue.dequeue()
                if packet:
                    return packet
        
        self.current_flow_index = (self.current_flow_index + 1) % len(self.flow_ids)
```

**队列管理策略**:
- 每个流维护独立队列（WFQ模式）
- 队列长度限制防止内存溢出
- 丢包统计用于性能分析

#### 2.2.3 Receiver组件
**主要功能**:
- 接收和统计数据包
- 支持统计模式和回发模式
- 生成性能分析数据

**统计数据收集**:
```python
def process_packet(self, data, addr, recv_time):
    packet = ProjectPacket.unpack(data)
    
    # 记录到统计系统
    self.flow_stats[packet.flow_id].record('packets_received', 1, recv_time,
                                          flow_id=packet.flow_id,
                                          size=packet.get_size())
    
    # 写入CSV日志
    self.data_log.write(f"{recv_time},{packet.flow_id},{packet.get_size()},{packet.seq_num},0\n")
```

### 2.3 调度算法分析

#### 2.3.1 FIFO算法
**优点**:
- 实现简单，开销低
- 保持数据包顺序
- 延迟抖动较小

**缺点**:
- 无法保证带宽公平性
- 大流量会饿死小流量
- 无法提供QoS保障

#### 2.3.2 简化WFQ算法
**优点**:
- 根据权重分配带宽
- 防止流量饿死现象
- 提供基本的QoS保障

**缺点**:
- 实现复杂度较高
- 额外的队列维护开销
- 可能增加延迟抖动

**权重分配机制**:
```
实际带宽分配比例 = 流权重 / 所有活跃流权重之和

例如：
Flow 1 (权重=1): 1/(1+1+2) = 25%
Flow 2 (权重=1): 1/(1+1+2) = 25%  
Flow 3 (权重=2): 2/(1+1+2) = 50%
```

### 2.4 性能监控与分析

#### 2.4.1 关键性能指标
- **吞吐量**: 各流的累计接收字节数
- **延迟**: 端到端包延迟统计
- **丢包率**: 队列溢出导致的丢包
- **公平性**: 带宽分配与权重的符合度

#### 2.4.2 数据可视化
使用matplotlib生成多种图表：
```python
def plot_throughput(flow_data, output_file, title):
    plt.figure(figsize=(12, 8))
    
    for flow_id in sorted(flow_data.keys()):
        # 计算累计字节数
        timestamps = []
        cumulative_bytes = []
        total_bytes = 0
        
        for timestamp, packet_size in flow_data[flow_id]:
            total_bytes += packet_size
            timestamps.append(timestamp)
            cumulative_bytes.append(total_bytes)
            
        plt.plot(timestamps, [b/1024 for b in cumulative_bytes], 
                label=f'Flow {flow_id}', linewidth=2)
    
    plt.xlabel('时间 (秒)')
    plt.ylabel('累计接收字节数 (KB)')
    plt.title(title)
    plt.legend()
    plt.grid(True)
    plt.savefig(output_file, dpi=300)
```

## 3. 实验设计

### 3.1 实验场景
按照课程要求设计的实验序列：

| 时间点 | 操作 | Flow 1 | Flow 2 | Flow 3 |
|--------|------|--------|--------|--------|
| T=0s   | 启动Flow 1 | ✓ (权重=1, 1024B) | - | - |
| T=2s   | 启动Flow 2 | ✓ | ✓ (权重=1, 512B) | - |
| T=4s   | 启动Flow 3 | ✓ | ✓ | ✓ (权重=2, 1024B) |
| T=6s   | 停止Flow 2 | ✓ | ✗ | ✓ |
| T=8s   | 停止所有 | ✗ | ✗ | ✗ |

### 3.2 期望结果分析
**FIFO算法期望**:
- 所有流平等竞争带宽
- 后启动的流可能获得更多带宽
- 权重设置不会影响实际分配

**WFQ算法期望**:
- T=2-4s: Flow 1和Flow 2各获得50%带宽
- T=4-6s: Flow 1获得25%，Flow 2获得25%，Flow 3获得50%
- T=6-8s: Flow 1获得33%，Flow 3获得67%

### 3.3 实验自动化
通过Shell脚本实现完全自动化的实验流程：
```bash
#!/bin/bash
# 启动组件
python3 src/receiver.py --mode stats --port $RECEIVER_PORT &
python3 src/router.py --algorithm $ALGORITHM --port $ROUTER_PORT &

# 按时序启动发送器
python3 src/sender.py --flow-id 1 --weight 1 --packet-size 1024 &
sleep 2
python3 src/sender.py --flow-id 2 --weight 1 --packet-size 512 &
sleep 2
python3 src/sender.py --flow-id 3 --weight 2 --packet-size 1024 &

# 按时序停止
sleep 2; kill $SENDER2_PID
sleep 2; kill $SENDER1_PID $SENDER3_PID
```

## 4. 工程实现细节

### 4.1 线程安全设计
- 使用`threading.Lock`保护共享数据结构
- 队列操作使用线程安全的`queue.Queue`
- 统计数据收集采用无锁设计

### 4.2 错误处理策略
```python
try:
    self.socket.sendto(packet_data, self.router_address)
    self.total_forwarded += 1
except Exception as e:
    self.logger.error(f"转发数据包失败: {e}")
    # 继续处理下一个包，不中断整个流程
```

### 4.3 资源管理
- 所有socket在程序结束时正确关闭
- 日志文件及时刷新和关闭
- 线程通过标志位优雅停止

### 4.4 配置灵活性
- 所有参数通过命令行传递
- 支持不同的端口和IP配置
- 可调整的带宽和队列大小限制

## 5. 测试与验证

### 5.1 单元测试
- 数据包打包/解包测试
- 速率控制算法测试
- 统计功能测试

### 5.2 集成测试
- 组件间通信测试
- 端到端延迟测试
- 长时间运行稳定性测试

### 5.3 性能验证
通过实验数据验证：
- WFQ算法是否实现了加权公平分配
- 延迟特性是否符合预期
- 系统在高负载下的表现

## 6. 结论与扩展

### 6.1 项目成果
- 成功实现了完整的网络调度算法对比系统
- 提供了直观的性能对比分析工具
- 验证了WFQ算法在公平性方面的优势

### 6.2 可能的扩展
- **算法扩展**: 实现DRR、SCFQ等其他调度算法
- **性能优化**: 使用更高效的数据结构和算法
- **功能增强**: 添加拥塞控制、流量整形等功能
- **可视化改进**: 实时图表显示和Web界面

### 6.3 学习收获
通过本项目的实现，深入理解了：
- 网络调度算法的原理和实现
- 系统性能测试和分析方法
- Python网络编程和多线程技术
- 数据可视化和实验自动化技术

本项目为网络QoS和调度算法的学习提供了一个完整的实践平台，具有很好的教学和研究价值。
