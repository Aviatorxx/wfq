# DRR (Deficit Round Robin) 路由器实现

这是一个基于Python实现的DRR（Deficit Round Robin）路由器项目，用于研究和演示DRR调度算法的工作原理。该项目包含完整的发送端、接收端和路由器实现，支持多流并发传输和基于权重的公平调度。

## 项目结构

```
src/
├── router_drr.py    # DRR路由器实现
├── sender.py        # 发送端实现
├── receiver.py      # 接收端实现
├── test_drr.py      # 测试脚本
├── common.py        # 公共定义
├── config.py        # 配置文件
├── plot.py          # 数据可视化
└── run_experiment.py # 实验运行脚本
```

## 功能特点

- 完整实现DRR调度算法
- 支持多流并发传输
- 基于权重的公平调度
- 实时流量统计和监控
- 详细的日志记录
- 支持RTT测量
- 可配置的测试场景

## 安装要求

- Python 3.6+
- 依赖包：
  - socket
  - threading
  - struct
  - logging
  - time
  - csv
  - os

## 快速开始

1. 启动接收器：
```bash
python src/receiver.py --mode log --router drr
```

2. 启动DRR路由器：
```bash
python src/router_drr.py
```

3. 运行测试脚本：
```bash
python src/test_drr.py
```

## 配置说明

主要配置参数（在`config.py`中）：

- `SENDER_BIND_IP`: 发送端绑定IP
- `ROUTER_IP`: 路由器IP
- `RECEIVER_IP`: 接收端IP
- `ROUTER_PORT_IN`: 路由器输入端口（默认9000）
- `ROUTER_PORT_OUT`: 路由器输出端口（默认9001）
- `RECEIVER_PORT`: 接收端端口（默认9002）
- `SENDER_PORT_BASE`: 发送端基础端口（默认10000）
- `PAYLOAD_MAX`: 最大负载大小（默认1400字节）

## DRR算法实现

DRR（Deficit Round Robin）算法的核心组件：

1. 数据结构：
   - 每个流维护独立的队列
   - 每个流有独立的量子值（quantum）
   - 每个流有独立的赤字计数器（deficit）

2. 调度机制：
   - 基于权重的量子值计算
   - 赤字累加和消耗
   - 轮转调度

3. 性能指标：
   - 包计数
   - 字节计数
   - 队列长度
   - RTT测量

## 测试场景

测试脚本（`test_drr.py`）提供了以下测试场景：

```python
flows = [
    (1, 1, 512, 0.001),   # 流1: 权重1, 包大小512字节, 间隔1ms
    (2, 2, 512, 0.001),   # 流2: 权重2, 包大小512字节, 间隔1ms
    (3, 4, 512, 0.001),   # 流3: 权重4, 包大小512字节, 间隔1ms
]
```

## 日志和监控

- 发送端日志：`logs/send_log_drr.csv`
- 接收端日志：`logs/recv_log_drr.csv`
- 路由器状态：每5秒输出一次统计信息

## 高级用法

1. 自定义测试场景：
```bash
python src/sender.py --flow 1 --weight 2 --size 1024 --rate 1.0 --dur 10.0 --mode drr
```

2. 运行完整实验：
```bash
python src/run_experiment.py
```

## 性能指标

- 包处理速率
- 队列长度
- 延迟分布
- 带宽利用率
- 公平性指标

## 注意事项

1. 确保端口未被占用
2. 检查防火墙设置
3. 确保有足够的系统资源
4. 建议在测试环境中运行

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 许可证

MIT License