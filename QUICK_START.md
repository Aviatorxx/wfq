# WFQ项目快速开始指南

## 🎯 项目概述

本项目实现了**FIFO**和**WFQ(加权公平队列)**调度算法的UDP网络通信系统，完全符合课程设计要求。

## 🚀 简单运行方式

### 使用启动脚本 (推荐)
```bash
./run.sh            # 显示选项菜单
./run.sh demo        # 快速演示
./run.sh stats       # Stats模式演示  
./run.sh full        # 完整对比实验
```

## 📊 三种主要实验模式

### 1. 快速演示 (20秒)
```bash
./scripts/demo.sh
# 或
./run.sh demo
```
- ✅ **功能**: 环境检查 + 基本测试 + Echo模式演示
- ✅ **特点**: 一站式验证，展示项目完整性
- ✅ **输出**: `results/demo/` 目录
- ✅ **用途**: 首次使用，快速验证项目功能

### 2. Stats模式演示 (60秒)
```bash
./scripts/stats_demo.sh
# 或  
./run.sh stats
```
- ✅ **功能**: 纯吞吐量分析，receiver不回发数据包
- ✅ **特点**: 展示课程要求的"模式1"特性
- ✅ **输出**: `results/stats/` 目录
- ✅ **用途**: 演示Stats模式的独特价值

### 3. 完整对比实验 (5分钟)
```bash
./scripts/full_comparison.sh
# 或
./run.sh full
```
- ✅ **功能**: FIFO vs WFQ完整对比分析
- ✅ **特点**: 按课程要求的精确时序实验
- ✅ **输出**: `results/experiments/` 目录
- ✅ **用途**: 课程答辩，满足所有课程要求

## 🔍 脚本功能对比

| 脚本 | 模式 | 算法 | 流数 | 时长 | 主要用途 |
|------|------|------|------|------|---------|
| **demo.sh** | Echo | FIFO | 2流 | 20秒 | 快速验证 |
| **stats_demo.sh** | Stats | FIFO | 3流 | 60秒 | 模式演示 |
| **full_comparison.sh** | Echo | FIFO+WFQ | 3流×2 | 5分钟 | 完整分析 |

## 📊 full_comparison.sh 的额外功能

相比单独的演示脚本，完整实验多包含：

### 1. 双算法完整对比
- ✅ FIFO算法完整实验
- ✅ WFQ算法完整实验  
- ✅ 算法性能对比图表

### 2. 课程精确实验设计
- ✅ T=0s: 启动Flow 1 (权重=1, 包大小=1024)
- ✅ T=2s: 启动Flow 2 (权重=1, 包大小=512)
- ✅ T=4s: 启动Flow 3 (权重=2, 包大小=1024)
- ✅ T=6s: 停止Flow 2
- ✅ T=8s: 停止所有流

### 3. 专业实验流程
- ✅ 完整的错误处理
- ✅ 自动进程管理
- ✅ 结果文件整理
- ✅ 综合分析报告

### 4. 完整结果输出
- ✅ algorithm_comparison.png - 算法对比图
- ✅ fifo_throughput.png - FIFO吞吐量图
- ✅ wfq_throughput.png - WFQ吞吐量图
- ✅ 延迟分布图和详细数据

## 📁 重组后的项目结构

```
wfq/
├── src/                          # 核心源码
├── scripts/ ✨                   # 所有实验脚本
│   ├── demo.sh                  # 快速演示
│   ├── stats_demo.sh            # Stats模式演示
│   ├── full_comparison.sh       # 完整对比实验
│   ├── run_fifo_experiment.sh   # FIFO单独实验
│   ├── run_wfq_experiment.sh    # WFQ单独实验
│   └── test_components.sh       # 组件测试
├── docs/                         # 文档
├── results/                      # 实验结果
├── run.sh ✨                    # 主启动脚本
├── README.md                     # 项目说明
├── QUICK_START.md               # 本文件
└── requirements.txt             # Python依赖
```

## 📋 查看结果

### 快速演示结果
```bash
open results/demo/demo_chart.png
ls results/demo/delays_flow_*.csv
```

### Stats模式结果
```bash
open results/stats/stats_throughput.png
cat results/stats/stats_received.log
```

### 完整实验结果
```bash
open results/experiments/algorithm_comparison.png
ls results/experiments/
```

## 🎯 推荐使用流程

### 首次使用 (完整验证)
1. `./run.sh demo` - 验证环境和基本功能
2. `./run.sh stats` - 验证Stats模式
3. `./run.sh full` - 运行完整实验

### 课程演示 (推荐)
1. `./run.sh demo` - 快速展示项目功能
2. `./run.sh full` - 完整的算法对比分析

### 快速验证
1. `./run.sh demo` - 仅验证项目是否正常工作

## 💡 重组优势

### 1. 逻辑清晰
- ✅ 所有脚本集中在scripts目录
- ✅ 功能分工明确，无重叠
- ✅ 命名直观，用途清晰

### 2. 使用简单
- ✅ 统一的启动脚本 `run.sh`
- ✅ 支持参数快速运行
- ✅ 清晰的选项菜单

### 3. 结构专业
- ✅ 符合标准项目组织方式
- ✅ 易于维护和扩展
- ✅ 更好的可读性

## 🏆 课程设计完整性

✅ **三个核心程序**: Sender, Router, Receiver  
✅ **双调度算法**: FIFO + WFQ  
✅ **双Receiver模式**: Echo + Stats  
✅ **完整实验设计**: 按课程要求时序  
✅ **全面结果分析**: 吞吐量 + 延迟图表  

**项目完全符合课程设计要求，可直接用于演示和答辩！** 🎉
