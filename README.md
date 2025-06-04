# WFQ网络调度算法对比系统

本项目实现了FIFO和WFQ（加权公平队列）调度算法的性能对比系统，通过UDP网络通信验证不同调度算法的特性。

## 🎯 项目概述

完整实现了课程设计的所有要求：
- ✅ 三个核心程序：Sender、Router、Receiver
- ✅ 双调度算法：FIFO 和 WFQ（加权公平队列）
- ✅ 双Receiver模式：Echo模式（延迟测量）+ Stats模式（吞吐量分析）
- ✅ UDP协议通信 + 24字节自定义项目头
- ✅ 完整的实验对比分析和可视化

## 🚀 快速开始

### 一键运行（推荐）
```bash
./run.sh            # 显示交互式菜单
./run.sh demo        # 快速演示 (20秒)
./run.sh stats       # Stats模式演示 (60秒)
./run.sh full        # 完整对比实验 (5分钟)
```

### 直接运行脚本
```bash
./scripts/demo.sh                # 快速功能演示
./scripts/stats_demo.sh          # Stats模式演示  
./scripts/full_comparison.sh     # 完整FIFO vs WFQ对比
```

## 📊 系统架构

```
┌─────────────┐    UDP     ┌─────────────┐    UDP     ┌─────────────┐
│   Sender    │ ──────────→│   Router    │ ──────────→│  Receiver   │
│             │            │             │            │             │
│ • 多流发送  │            │ • FIFO调度  │            │ • 数据统计  │
│ • 速率控制  │            │ • WFQ调度   │            │ • 延迟测量  │
│ • 延迟测量  │            │ • 带宽限制  │            │ • 结果记录  │
└─────────────┘            └─────────────┘            └─────────────┘
```

## 🔧 核心特性

### 24字节项目头格式
```
┌─────────────┬─────────────┬──────────┬──────────┬────────┬─────────┬─────────┐
│  源IP(4B)   │  目标IP(4B) │ 源端口(2B) │目标端口(2B)│ 权重(4B) │ 流ID(4B) │序列号(4B)│
└─────────────┴─────────────┴──────────┴──────────┴────────┴─────────┴─────────┘
```

### 调度算法
- **FIFO**: 单一队列，先进先出，无法保证公平性
- **WFQ**: 每流独立队列，加权轮询调度，实现权重比例分配

### Receiver双模式
- **Stats模式**（课程要求模式1）: 记录统计信息，生成"bytes vs time"图表
- **Echo模式**（课程要求模式2）: 回发数据包，支持延迟测量，生成"packets vs delay"图表

## 📁 项目结构

```
wfq/
├── src/                          # 核心源码
│   ├── sender.py                # UDP发送器
│   ├── receiver.py              # 双模式接收器
│   ├── router.py                # FIFO/WFQ路由器
│   ├── packet_format.py         # 24字节项目头格式
│   ├── utils.py                 # 工具函数和速率控制
│   └── analyze_results.py       # 结果分析脚本
├── scripts/                      # 实验脚本
│   ├── demo.sh                  # 快速演示
│   ├── stats_demo.sh            # Stats模式演示
│   ├── full_comparison.sh       # 完整对比实验
│   ├── run_fifo_experiment.sh   # FIFO实验
│   ├── run_wfq_experiment.sh    # WFQ实验
│   └── test_components.sh       # 组件测试
├── results/                      # 实验结果
│   ├── demo/                    # demo.sh 输出
│   ├── stats/                   # stats_demo.sh 输出
│   ├── experiments/             # full_comparison.sh 输出
│   └── README.md                # 结果目录说明
├── docs/                         # 文档
│   └── design_report.md         # 技术设计报告
├── run.sh                        # 主启动脚本
├── README.md                     # 本文件
├── QUICK_START.md               # 快速开始指南
└── requirements.txt             # Python依赖
```

## 🧪 实验设计

按照课程要求实现以下实验序列：
- **T=0s**: 启动Flow 1 (权重=1, 包大小=1024字节)
- **T=2s**: 启动Flow 2 (权重=1, 包大小=512字节)
- **T=4s**: 启动Flow 3 (权重=2, 包大小=1024字节)
- **T=6s**: 停止Flow 2
- **T=8s**: 停止所有流

## 📈 实验结果

系统生成完整的分析结果：
- **吞吐量对比**: 各流的累计接收字节数随时间变化
- **延迟分析**: 真实的端到端延迟分布
- **算法对比**: FIFO vs WFQ综合性能分析图表
- **公平性验证**: 验证WFQ算法的权重分配效果

## 🎯 技术亮点

- **精确速率控制**: 使用令牌桶算法实现精确的发送速率控制
- **完整错误处理**: 健全的异常处理和资源管理机制
- **自动化实验**: 全流程自动化，从启动到结果分析
- **专业可视化**: 自动生成专业的数据分析图表
- **模块化设计**: 清晰的代码结构，便于维护和扩展

## 🎓 课程要求对照

| 课程要求 | 实现状态 | 说明 |
|----------|----------|------|
| 三个核心程序 | ✅ 完成 | Sender, Router, Receiver |
| WFQ调度算法 | ✅ 完成 | 加权公平队列完整实现 |
| UDP协议通信 | ✅ 完成 | 24字节项目头 + 数据负载 |
| Receiver模式1 | ✅ 完成 | Stats模式（吞吐量统计） |
| Receiver模式2 | ✅ 完成 | Echo模式（延迟测量） |
| bytes vs time图 | ✅ 完成 | 多种吞吐量图表 |
| packets vs delay图 | ✅ 完成 | 延迟分布分析图 |
| 算法对比实验 | ✅ 完成 | FIFO vs WFQ完整对比 |

## 🛠️ 环境要求

- Python 3.7+
- 依赖包: `pip3 install matplotlib numpy`

## 📖 使用指南

详细使用说明请参考：
- [QUICK_START.md](QUICK_START.md) - 快速开始指南
- [results/README.md](results/README.md) - 结果目录结构说明
- [docs/design_report.md](docs/design_report.md) - 技术设计报告

## 🎉 项目特色

本项目不仅完整实现了课程设计要求，更体现了：
- **技术完整性**: 从底层协议到上层应用的全栈实现
- **工程规范性**: 模块化设计、完整测试、详细文档
- **实用价值**: 可用于网络调度算法研究和教学的实用工具

---

*WFQ网络调度算法对比系统 - 完全符合课程设计要求的高质量实现*
