#!/usr/bin/env bash
python src/receiver.py --mode echo --router rr   &
R_PID=$!
python src/router_rr.py                &
RT_PID=$!

sleep 1
# Flow 1
python src/sender.py --flow 1 --weight 1 --size 1024 --rate 1 --dur 8 --mode rr &
# Flow 2 (晚 2 秒启动)
sleep 2
python src/sender.py --flow 2 --weight 1 --size 512  --rate 1 --dur 6 --mode rr &
# Flow 3
sleep 2
python src/sender.py --flow 3 --weight 2 --size 1024 --rate 1 --dur 4 --mode rr &

wait
kill $R_PID $RT_PID

# 生成图表
echo "生成累积字节图..."
python src/plot.py logs/recv_log_rr.csv --title "RR cumulative bytes" --type bytes

echo "生成RTT延迟图..."
python src/plot.py logs/send_log_rr.csv --title "RR packet delay" --type rtt