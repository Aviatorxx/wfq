# WFQ实验结果目录结构

## 📁 目录功能说明

### `demo/` - Demo演示结果 
**脚本**: `./scripts/demo.sh` (20秒快速演示)
- `demo_chart.png` - 演示图表
- `demo_received.log` - 接收数据日志
- `delays_flow_*.csv` - 真实延迟数据 (echo模式)
- `demo_*.log` - 各组件运行日志

### `stats/` - Stats模式结果
**脚本**: `./scripts/stats_demo.sh` (60秒吞吐量分析)
- `stats_received.log` - 接收统计数据
- `stats_throughput.png` - 吞吐量图表
- `stats_*.log` - 各组件运行日志
- **特点**: 纯统计模式，receiver不回发包

### `experiments/` - 完整实验结果 
**脚本**: `./scripts/full_comparison.sh` (5分钟完整对比)
- `algorithm_comparison.png` - **FIFO vs WFQ综合对比图** ⭐
- `fifo_throughput.png` / `wfq_throughput.png` - 各算法吞吐量图
- `fifo_delays.png` / `wfq_delays.png` - 各算法延迟分布图
- `fifo_received_data.log` / `wfq_received_data.log` - 接收数据
- `fifo_delays_flow_*.csv` / `wfq_delays_flow_*.csv` - 延迟数据
- `fifo_*.log` / `wfq_*.log` - 详细运行日志

### `logs/` - 系统日志
- 各种系统级别的运行日志

## 🎯 使用建议

### 快速验证项目功能
```bash
./scripts/demo.sh
# 查看: results/demo/demo_chart.png
```

### 演示Stats模式特性
```bash  
./scripts/stats_demo.sh
# 查看: results/stats/stats_throughput.png
```

### 完整课程要求实验
```bash
./scripts/full_comparison.sh  
# 查看: results/experiments/algorithm_comparison.png
```

## 📊 目录分离的优势

### 1. 结果不混淆
- 每种实验有独立目录
- 避免文件覆盖问题
- 便于结果对比分析

### 2. 功能明确
- `demo/`: 功能演示和验证
- `stats/`: Stats模式特性展示  
- `experiments/`: 完整的算法对比研究

### 3. 符合预期
- 与脚本名称和功能对应
- 便于查找特定类型的结果
- 清晰的实验组织结构

## 🔍 查看结果的建议顺序

1. **首次运行**: `demo/` → 验证项目是否正常工作
2. **模式理解**: `stats/` → 理解Stats模式的特点
3. **完整分析**: `experiments/` → 查看最终的算法对比结果

每个目录的结果都是独立完整的，可以根据需要单独查看分析。
