#!/bin/bash
# Stats模式 - 纯吞吐量分析 (不测量延迟)
echo "=================================================="
echo "       WFQ Stats模式 (吞吐量分析)"
echo "=================================================="

cd /Users/aviator/Documents/MCP/wfq
mkdir -p results/stats

# 清理旧文件
rm -f results/stats/*

echo "启动Stats模式组件..."

# Receiver (stats模式 - 不回发包)
python3 src/receiver.py --mode stats --port 9999 --log-file stats/stats_received.log > results/stats/stats_receiver.log 2>&1 &
RECEIVER_PID=$!
sleep 2

# Router (FIFO算法用于对比)
python3 src/router.py --algorithm fifo --bandwidth 200 --port 8888 > results/stats/stats_router.log 2>&1 &
ROUTER_PID=$!
sleep 2

# 按课程要求的时序启动多个流
echo "启动Flow 1 (权重=1, 1024字节)..."
python3 src/sender.py --flow-id 1 --weight 1 --packet-size 1024 --rate 20480 \
    --duration 12 --log-file results/stats/stats_sender1.log > results/stats/stats_sender1_output.log 2>&1 &
SENDER1_PID=$!

sleep 2
echo "启动Flow 2 (权重=1, 512字节)..."
python3 src/sender.py --flow-id 2 --weight 1 --packet-size 512 --rate 15360 \
    --duration 6 --log-file results/stats/stats_sender2.log > results/stats/stats_sender2_output.log 2>&1 &
SENDER2_PID=$!

sleep 2
echo "启动Flow 3 (权重=2, 1024字节)..."
python3 src/sender.py --flow-id 3 --weight 2 --packet-size 1024 --rate 30720 \
    --duration 8 --log-file results/stats/stats_sender3.log > results/stats/stats_sender3_output.log 2>&1 &
SENDER3_PID=$!

echo "运行中... (15秒)"
sleep 15

# 停止所有组件
echo "停止组件..."
kill $SENDER1_PID $SENDER2_PID $SENDER3_PID $ROUTER_PID $RECEIVER_PID 2>/dev/null

# 生成吞吐量图表
echo "生成吞吐量图表..."
python3 -c "
import sys
sys.path.append('src')
from utils import DataAnalyzer
DataAnalyzer.plot_throughput_vs_time(
    'results/stats/stats_received.log',
    'results/stats/stats_throughput.png',
    'Stats模式 - 吞吐量分析 (FIFO算法)'
)
print('✓ 图表已生成: results/stats/stats_throughput.png')
" 2>/dev/null || echo "⚠️ 图表生成失败"

echo ""
echo "✅ Stats模式完成！"
echo "查看结果: results/stats/"
echo "- 吞吐量数据: stats_received.log"
echo "- 吞吐量图表: stats_throughput.png"
echo "- 特点: 纯统计模式，无延迟测量"
