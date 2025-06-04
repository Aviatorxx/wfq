#!/bin/bash

# 简单测试脚本 - 验证各个组件是否能正常工作

echo "=================================================="
echo "           WFQ项目组件测试"
echo "=================================================="

cd /Users/aviator/Documents/MCP/wfq

# 测试1：检查Python依赖
echo "测试1：检查Python环境和依赖..."
python3 -c "
import sys
print(f'Python版本: {sys.version}')
try:
    import matplotlib
    print('✓ matplotlib 可用')
except ImportError:
    print('✗ matplotlib 不可用，请安装: pip3 install matplotlib')

try:
    import numpy
    print('✓ numpy 可用')
except ImportError:
    print('✗ numpy 不可用，请安装: pip3 install numpy')

import socket
print('✓ socket 模块可用')
import threading
print('✓ threading 模块可用')
import queue
print('✓ queue 模块可用')
"

echo ""

# 测试2：测试数据包格式
echo "测试2：测试数据包格式..."
python3 -c "
import sys
sys.path.append('src')
from packet_format import ProjectPacket

# 创建测试数据包
packet = ProjectPacket(
    src_ip='192.168.1.1',
    dst_ip='192.168.1.2',
    src_port=12345,
    dst_port=8080,
    weight=2,
    flow_id=1,
    seq_num=100,
    data=b'Hello Test!'
)

print(f'✓ 数据包创建成功: {packet}')

# 测试打包和解包
packed = packet.pack()
unpacked = ProjectPacket.unpack(packed)

print(f'✓ 打包后大小: {len(packed)} 字节')
print(f'✓ 解包后: Flow {unpacked.flow_id}, Seq {unpacked.seq_num}')

if packet.flow_id == unpacked.flow_id and packet.seq_num == unpacked.seq_num:
    print('✓ 数据包格式测试通过')
else:
    print('✗ 数据包格式测试失败')
"

echo ""

# 测试3：测试工具函数
echo "测试3：测试工具函数..."
python3 -c "
import sys
sys.path.append('src')
from utils import RateLimiter, Statistics

# 测试速率限制器
limiter = RateLimiter(1000)  # 1000 字节/秒
print('✓ 速率限制器创建成功')

wait_time = limiter.consume(100)
print(f'✓ 消费100字节，等待时间: {wait_time:.3f}秒')

# 测试统计模块
stats = Statistics()
stats.record('test_metric', 42, 1234567890.0)
data = stats.get_data('test_metric')
print(f'✓ 统计模块测试通过，记录数量: {len(data)}')
"

echo ""

# 测试4：快速功能测试
echo "测试4：快速功能测试（5秒）..."

# 启动简单的receiver
echo "启动测试receiver..."
python3 src/receiver.py --mode stats --port 9999 --log-file test_received.log &
RECEIVER_PID=$!
sleep 1

# 启动简单的router
echo "启动测试router..."
python3 src/router.py --algorithm fifo --bandwidth 100 --port 8888 --receiver-ip 127.0.0.1 --receiver-port 9999 &
ROUTER_PID=$!
sleep 1

# 发送一些测试数据包
echo "发送测试数据包..."
python3 src/sender.py --flow-id 1 --weight 1 --packet-size 512 --rate 10240 --router-ip 127.0.0.1 --router-port 8888 --duration 3 &
SENDER_PID=$!

# 等待测试完成
sleep 4

# 停止所有组件
echo "停止测试组件..."
kill $SENDER_PID $ROUTER_PID $RECEIVER_PID 2>/dev/null
wait $SENDER_PID $ROUTER_PID $RECEIVER_PID 2>/dev/null

# 检查是否生成了结果文件
if [ -f "results/test_received.log" ]; then
    echo "✓ 功能测试通过 - 成功生成接收数据日志"
    
    # 显示一些统计信息
    lines=$(wc -l < results/test_received.log)
    echo "  接收数据记录数: $((lines-1))"  # 减去标题行
else
    echo "✗ 功能测试失败 - 未找到接收数据日志"
fi

# 清理测试文件
rm -f results/test_received.log results/delays_flow_1.csv

echo ""
echo "=================================================="
echo "测试完成！"
echo ""
echo "如果所有测试都通过，可以运行完整实验："
echo "  ./scripts/run_all_experiments.sh"
echo ""
echo "或者分别运行FIFO和WFQ实验："
echo "  ./scripts/run_fifo_experiment.sh"
echo "  ./scripts/run_wfq_experiment.sh"
echo "=================================================="
