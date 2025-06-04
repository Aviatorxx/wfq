#!/bin/bash

# WFQ算法实验脚本 - 修正版
# 文件直接生成到正确目录，避免混乱

echo "=== 开始WFQ实验（文件自动分类版）==="

# 设置实验参数
ROUTER_PORT=8081
RECEIVER_PORT=9091
RECEIVER_IP="127.0.0.1"
ROUTER_IP="127.0.0.1"
BANDWIDTH=500  # KB/s

# 创建完整目录结构
mkdir -p /Users/aviator/Documents/MCP/wfq/results/experiments/{charts,data,logs}

# 清理之前的WFQ结果
rm -f /Users/aviator/Documents/MCP/wfq/results/experiments/*/wfq_*
rm -f /Users/aviator/Documents/MCP/wfq/results/*.log

echo "📋 实验设计："
echo "   ✅ 图表输出 → experiments/charts/"
echo "   ✅ 数据输出 → experiments/data/"
echo "   ✅ 日志输出 → experiments/logs/"
echo "   ✅ 无临时文件混乱"
echo ""

# 启动Receiver (直接输出到正确位置)
echo "启动Receiver (Echo模式)..."
cd /Users/aviator/Documents/MCP/wfq
python3 src/receiver.py \
    --mode echo \
    --port $RECEIVER_PORT \
    --log-file experiments/data/wfq_received_data.log \
    > results/experiments/logs/wfq_receiver.log 2>&1 &
RECEIVER_PID=$!
sleep 2

# 启动Router (直接输出到正确位置)
echo "启动Router (WFQ)..."
python3 src/router.py \
    --algorithm wfq \
    --bandwidth $BANDWIDTH \
    --port $ROUTER_PORT \
    --receiver-ip $RECEIVER_IP \
    --receiver-port $RECEIVER_PORT \
    > results/experiments/logs/wfq_router.log 2>&1 &
ROUTER_PID=$!
sleep 2

echo "开始实验序列..."

# Sender 1 (直接输出到logs目录)
echo "启动Sender 1 (Flow 1, Weight 1, Size 1024)"
python3 src/sender.py \
    --flow-id 1 --weight 1 --packet-size 1024 --rate 51200 \
    --router-ip $ROUTER_IP --router-port $ROUTER_PORT --duration 16 \
    --log-file results/experiments/logs/wfq_sender1.log \
    > results/experiments/logs/wfq_sender1_output.log 2>&1 &
SENDER1_PID=$!

sleep 2
echo "启动Sender 2 (Flow 2, Weight 1, Size 512)"
python3 src/sender.py \
    --flow-id 2 --weight 1 --packet-size 512 --rate 25600 \
    --router-ip $ROUTER_IP --router-port $ROUTER_PORT --duration 8 \
    --log-file results/experiments/logs/wfq_sender2.log \
    > results/experiments/logs/wfq_sender2_output.log 2>&1 &
SENDER2_PID=$!

sleep 2  
echo "启动Sender 3 (Flow 3, Weight 2, Size 1024)"
python3 src/sender.py \
    --flow-id 3 --weight 2 --packet-size 1024 --rate 102400 \
    --router-ip $ROUTER_IP --router-port $ROUTER_PORT --duration 10 \
    --log-file results/experiments/logs/wfq_sender3.log \
    > results/experiments/logs/wfq_sender3_output.log 2>&1 &
SENDER3_PID=$!

sleep 2
echo "停止Sender 2"
kill $SENDER2_PID 2>/dev/null

sleep 2
echo "停止所有Sender"
kill $SENDER1_PID $SENDER3_PID 2>/dev/null

# 等待完成
wait $SENDER1_PID $SENDER2_PID $SENDER3_PID 2>/dev/null
echo "等待数据处理完成..."
sleep 3

# 停止组件
echo "停止Router和Receiver"
kill $ROUTER_PID $RECEIVER_PID 2>/dev/null
wait $ROUTER_PID $RECEIVER_PID 2>/dev/null

echo "=== WFQ实验完成 ==="

# 重命名延迟文件以区分算法
echo "📊 整理延迟数据文件..."
cd /Users/aviator/Documents/MCP/wfq/results/experiments/data
for flow in 1 2 3; do
    if [ -f "delays_flow_${flow}.csv" ]; then
        mv "delays_flow_${flow}.csv" "wfq_delays_flow_${flow}.csv"
        echo "   ✅ delays_flow_${flow}.csv → wfq_delays_flow_${flow}.csv"
    fi
done

# 清理临时文件
cd /Users/aviator/Documents/MCP/wfq/results
rm -f receiver_*.log router_*.log *.txt 2>/dev/null

# 生成图表（直接输出到charts目录）
echo "📈 生成WFQ图表..."
cd /Users/aviator/Documents/MCP/wfq/results/experiments
python3 ../../src/analyze_results.py \
    --algorithm wfq \
    --data-file data/wfq_received_data.log \
    --output-dir charts 2>/dev/null || echo "   ⚠️ 图表生成失败，但数据已保存"

# 验证结果
echo ""
echo "✅ WFQ实验完成！文件结构："
echo ""
echo "📊 图表文件 (charts/):"
ls -la /Users/aviator/Documents/MCP/wfq/results/experiments/charts/wfq_* 2>/dev/null | sed 's/^/   /' || echo "   (等待图表生成)"
echo ""
echo "📄 数据文件 (data/):"  
ls -la /Users/aviator/Documents/MCP/wfq/results/experiments/data/wfq_* 2>/dev/null | sed 's/^/   /'
echo ""
echo "📋 日志文件 (logs/):"
ls -la /Users/aviator/Documents/MCP/wfq/results/experiments/logs/wfq_* 2>/dev/null | head -3 | sed 's/^/   /'
echo "   ... (更多日志文件)"
echo ""

echo "🎯 关键改进："
echo "   • 文件生成时就自动分类到正确目录"
echo "   • 避免了后期手动整理的混乱"  
echo "   • 清理了所有临时文件"
echo "   • 符合课程要求的Echo模式和延迟测量"