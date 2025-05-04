#!/bin/bash

set -euo pipefail
trap 'kill ${ROUTER_PID:-} ${RECEIVER_PID:-} 2>/dev/null || true' EXIT

# 切换到脚本所在目录的上一级（即项目根目录）
#cd "$(dirname "$0")/.."

# 清理上一轮实验残留日志
rm -f logs/recv_log_drr.csv logs/send_log_drr.csv

# 激活conda环境
source $(conda info --base)/etc/profile.d/conda.sh
conda activate wfq-sim

# 启动接收端
python src/receiver.py --mode echo --router drr &
RECEIVER_PID=$!

# 启动DRR路由器
python src/router_drr.py &
ROUTER_PID=$!

sleep 1

# 启动发送端
python src/sender.py --flow 1 --weight 1 --size 1024 --rate 4.5 --dur 10 --mode drr &
SENDER1_PID=$!

sleep 2
python src/sender.py --flow 2 --weight 1 --size 512 --rate 4.5 --dur 6 --mode drr &
SENDER2_PID=$!

sleep 2
python src/sender.py --flow 3 --weight 2 --size 1024 --rate 4.5 --dur 6 --mode drr &
SENDER3_PID=$!

wait $SENDER1_PID $SENDER2_PID $SENDER3_PID

sleep 1
kill -INT $ROUTER_PID $RECEIVER_PID

# 生成图表
echo "生成累积字节图..."
python src/plot.py logs/recv_log_drr.csv --title "DRR累积字节" --type bytes

#echo "生成RTT延迟图..."
#python src/plot.py logs/send_log_drr.csv --title "DRR包延迟" --type rtt

echo "生成累积字节与带宽图..."
python src/plot.py logs/recv_log_drr.csv --title "DRR累积字节与带宽" --type bytes_rate