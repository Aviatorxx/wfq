#!/bin/bash

# 激活conda环境
source $(conda info --base)/etc/profile.d/conda.sh
conda activate wfq-sim

# 启动接收端
python src/receiver.py --mode echo --router rr &
RECEIVER_PID=$!

# 启动RR路由器
python src/router_rr.py &
ROUTER_PID=$!

# 等待路由器启动
sleep 1

# 启动发送端
# Flow 1: 权重=1, 包大小=1024
python src/sender.py --flow 1 --weight 1 --size 1024 --rate 1 --dur 10 --mode rr &
SENDER1_PID=$!

# Flow 2: 权重=1, 包大小=512
sleep 2
python src/sender.py --flow 2 --weight 1 --size 512 --rate 1 --dur 6 --mode rr &
SENDER2_PID=$!

# Flow 3: 权重=2, 包大小=1024
sleep 2
python src/sender.py --flow 3 --weight 2 --size 1024 --rate 1 --dur 6 --mode rr &
SENDER3_PID=$!

# 等待所有发送端完成
wait $SENDER1_PID $SENDER2_PID $SENDER3_PID

# 清理
kill $ROUTER_PID $RECEIVER_PID

# 生成图表
echo "生成累积字节图..."
python src/plot.py logs/recv_log_rr.csv --title "RR cumulative bytes" --type bytes

echo "生成RTT延迟图..."
python src/plot.py logs/send_log_rr.csv --title "RR packet delay" --type rtt

echo "生成累积字节与带宽图..."
python src/plot.py logs/recv_log_rr.csv --title "RR累积字节与带宽" --type bytes_rate