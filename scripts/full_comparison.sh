#!/bin/bash

# 主实验脚本 - 修正版
# FIFO vs WFQ完整对比，文件自动分类

echo "=================================================="
echo "        网络调度算法对比实验"
echo "        FIFO vs WFQ (Weighted Fair Queuing)"
echo "=================================================="

cd /Users/aviator/Documents/MCP/wfq

# 创建完整的结果目录结构
mkdir -p results/experiments/{charts,data,logs}

echo ""
echo "实验将按以下顺序进行："
echo "1. FIFO调度算法实验"
echo "2. WFQ调度算法实验"  
echo "3. 生成算法对比图表"
echo ""

# 运行FIFO实验
echo "=========================================="
echo "第1步：运行FIFO调度算法实验"
echo "=========================================="
chmod +x scripts/run_fifo_experiment.sh
./scripts/run_fifo_experiment.sh

if [ $? -ne 0 ]; then
    echo "错误：FIFO实验执行失败"
    exit 1
fi

echo ""
echo "FIFO实验完成，等待5秒后开始WFQ实验..."
sleep 5

# 运行WFQ实验
echo "=========================================="
echo "第2步：运行WFQ调度算法实验" 
echo "=========================================="
chmod +x scripts/run_wfq_experiment.sh
./scripts/run_wfq_experiment.sh

if [ $? -ne 0 ]; then
    echo "错误：WFQ实验执行失败"
    exit 1
fi

echo ""
echo "WFQ实验完成，等待3秒后生成对比图表..."
sleep 3

# 生成算法对比图表
echo "=========================================="
echo "第3步：生成算法对比分析图表"
echo "=========================================="
cd results/experiments
python3 ../../src/analyze_results.py \
    --generate-comparison \
    --experiments-dir . \
    --output-dir charts 2>/dev/null || echo "对比图表生成失败，但实验数据已保存"
cd ../..

# 显示结果摘要
echo ""
echo "=================================================="
echo "               实验完成！"
echo "=================================================="
echo ""
echo "📁 实验结果已保存到 results/experiments/ 目录："
echo ""

# 检查并列出生成的文件
echo "📊 图表文件 (charts/):"
if [ -f "results/experiments/charts/algorithm_comparison.png" ]; then
    echo "   ✅ algorithm_comparison.png    - 算法对比图表 ⭐ 最重要"
fi

if [ -f "results/experiments/charts/fifo_throughput.png" ]; then
    echo "   ✅ fifo_throughput.png         - FIFO吞吐量图"
fi

if [ -f "results/experiments/charts/wfq_throughput.png" ]; then
    echo "   ✅ wfq_throughput.png          - WFQ吞吐量图"
fi

if [ -f "results/experiments/charts/fifo_delays.png" ]; then
    echo "   ✅ fifo_delays.png             - FIFO延迟图"
fi

if [ -f "results/experiments/charts/wfq_delays.png" ]; then
    echo "   ✅ wfq_delays.png              - WFQ延迟图"
fi

echo ""
echo "📄 数据文件 (data/):"
echo "   ✅ fifo_received_data.log       - FIFO接收数据"
echo "   ✅ wfq_received_data.log        - WFQ接收数据"
echo "   ✅ *_delays_flow_*.csv          - 各流延迟数据"

echo ""
echo "📋 日志文件 (logs/):"
echo "   ✅ *_router.log                 - Router运行日志"
echo "   ✅ *_sender*.log                - Sender运行日志"
echo "   ✅ *_receiver.log               - Receiver运行日志"

echo ""
echo "=================================================="
echo "实验分析建议："
echo ""
echo "1. 查看 charts/algorithm_comparison.png 了解两种算法的整体对比"
echo "2. 对比 FIFO 和 WFQ 的吞吐量图，观察带宽分配差异"
echo "3. 查看延迟数据和图表分析性能差异"
echo "4. 如需快速演示，可运行 ./scripts/demo.sh"
echo ""
echo "重点观察："
echo "- WFQ算法是否实现了基于权重的公平带宽分配"
echo "- 各流在不同时间段的吞吐量变化"
echo "- 高权重流（Flow 3）是否获得了更多带宽"
echo "- FIFO vs WFQ在延迟和吞吐量上的差异"
echo ""
echo "🎯 文件管理改进："
echo "- 所有文件自动分类到正确目录"
echo "- 图表、数据、日志分离清晰"
echo "- 无临时文件混乱"
echo "- 便于答辩展示"
echo "=================================================="