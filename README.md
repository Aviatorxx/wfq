# 加权公平队列 (WFQ) 实现

本项目实现了一个基于UDP的网络流量调度系统，包括发送端、路由器和接收端，用于演示和比较不同调度算法（FIFO和RR）的性能差异。

## 项目结构

```
wfq/ 
 │ 
 ├─ src/                     # 代码 
 │   ├─ config.py            # 统一端口/IP/速率等参数 
 │   ├─ common.py            # 公用函数：打日志、时间戳、ProjectHeader 结构 
 │   ├─ sender.py            # 发送端 
 │   ├─ receiver.py          # 接收 & 回包 
 │   ├─ router.py            # FIFO调度 
 │   ├─ router_rr.py         # 轮询(Round Robin)调度 
 │   └─ plot.py              # 读 CSV 画图 
 │ 
 ├─ scripts/                 # 一键实验脚本 
 │   ├─ run_fifo.sh          # 运行FIFO实验 
 │   └─ run_rr.sh            # 运行RR实验 
 │ 
 ├─ logs/                    # 运行期生成 
 │   ├─ recv_log_fifo.csv    # FIFO接收日志 
 │   ├─ send_log_fifo.csv    # FIFO发送日志 
 │   ├─ recv_log_rr.csv      # RR接收日志 
 │   └─ send_log_rr.csv      # RR发送日志 
 │ 
 ├─ environment.yml         # 环境配置 
 └─ README.md               # 项目说明 
```

## 功能说明

### 发送端 (sender.py)

- 按指定速率发送UDP数据包
- 支持设置流ID、权重、包大小等参数
- 接收回包并计算RTT延迟

### 接收端 (receiver.py)

- 支持两种模式：log（仅记录）和echo（回包）
- 记录接收到的数据包信息（时间戳、流ID、大小）

### 路由器

- FIFO路由器 (router.py)：先进先出队列
- RR路由器 (router_rr.py)：轮询调度算法

### 数据分析 (plot.py)

- 绘制累积字节图：展示不同流随时间的数据传输量
- 绘制RTT延迟图：展示不同流的数据包延迟情况

## 使用方法

### 运行FIFO实验

```bash
bash scripts/run_fifo.sh
```

### 运行RR实验

```bash
bash scripts/run_rr.sh
```

### 手动运行组件

1. 启动接收端：
   ```bash
   python src/receiver.py --mode echo --router fifo
   ```

2. 启动路由器：
   ```bash
   python src/router.py  # FIFO路由器
   # 或
   python src/router_rr.py  # RR路由器
   ```

3. 启动发送端：
   ```bash
   python src/sender.py --flow 1 --weight 1 --size 1024 --rate 1 --dur 10 --mode fifo
   ```

4. 绘制图表：
   ```bash
   # 绘制累积字节图
   python src/plot.py logs/recv_log_fifo.csv --title "FIFO cumulative bytes" --type bytes
   
   # 绘制RTT延迟图
   python src/plot.py logs/send_log_fifo.csv --title "FIFO packet delay" --type rtt
   ```

## 实验设计

实验按以下步骤进行：

1. 启动Flow 1（权重=1，包大小=1024）
2. 2秒后，启动Flow 2（权重=1，包大小=512）
3. 再过2秒，启动Flow 3（权重=2，包大小=1024）
4. 2秒后，停止Flow 2
5. 再过2秒，停止所有流

通过比较FIFO和RR两种调度算法下的累积字节图和RTT延迟图，可以观察不同调度算法对网络流量的影响。