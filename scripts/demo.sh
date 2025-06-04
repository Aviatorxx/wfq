#!/bin/bash

# WFQ项目快速演示脚本
# 运行一个简化的演示来展示系统功能

echo "=================================================="
echo "       WFQ网络调度算法演示"
echo "=================================================="

cd /Users/aviator/Documents/MCP/wfq

# 创建demo结果目录
mkdir -p results/demo

echo "正在检查Python环境..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

echo "✓ Python3 已安装: $(python3 --version)"

# 检查必需的包
echo "检查必需的包..."
python3 -c "import matplotlib, numpy; print('✓ 所需包已安装')" 2>/dev/null || {
    echo "❌ 缺少必需的包，正在安装..."
    pip3 install matplotlib numpy
}

# 设置脚本权限
echo "设置脚本权限..."
chmod +x scripts/*.sh

# 运行基本测试
echo ""
echo "=========================================="
echo "1. 运行基本组件测试"
echo "=========================================="

python3 -c "
import sys
sys.path.insert(0, 'src')

print('测试数据包格式...')
try:
    from packet_format import ProjectPacket
    packet = ProjectPacket(flow_id=1, seq_num=1, data=b'test')
    packed = packet.pack()
    unpacked = ProjectPacket.unpack(packed)
    assert packet.flow_id == unpacked.flow_id
    print('✓ 数据包格式测试通过')
except Exception as e:
    print(f'✗ 数据包测试失败: {e}')
    exit(1)

print('测试工具函数...')
try:
    from utils import RateLimiter, Statistics
    limiter = RateLimiter(1000)
    stats = Statistics()
    print('✓ 工具函数测试通过')
except Exception as e:
    print(f'✗ 工具函数测试失败: {e}')
    exit(1)

print('✓ 基本组件测试通过')
"

if [ $? -ne 0 ]; then
    echo "❌ 基本测试失败，请检查代码"
    exit 1
fi

echo ""
echo "=========================================="
echo "2. 运行快速功能演示 (20秒)"
echo "=========================================="

echo "启动演示组件..."

# 启动receiver (echo模式用于延迟测量)
echo "启动Receiver (echo模式)..."
python3 src/receiver.py --mode echo --port 9999 --log-file demo/demo_received.log > results/demo/demo_receiver.log 2>&1 &
RECEIVER_PID=$!
sleep 2

# 启动router (FIFO)
echo "启动Router (FIFO算法)..."
python3 src/router.py --algorithm fifo --bandwidth 200 --port 8888 --receiver-ip 127.0.0.1 --receiver-port 9999 > results/demo/demo_router.log 2>&1 &
ROUTER_PID=$!
sleep 2

# 启动两个sender进行演示
echo "启动演示流量..."

# Flow 1: 权重1, 1024字节包
python3 src/sender.py --flow-id 1 --weight 1 --packet-size 1024 --rate 20480 --router-ip 127.0.0.1 --router-port 8888 --duration 10 --log-file results/demo/demo_sender1.log > results/demo/demo_sender1_output.log 2>&1 &
SENDER1_PID=$!

sleep 3

# Flow 2: 权重2, 512字节包  
python3 src/sender.py --flow-id 2 --weight 2 --packet-size 512 --rate 15360 --router-ip 127.0.0.1 --router-port 8888 --duration 8 --log-file results/demo/demo_sender2.log > results/demo/demo_sender2_output.log 2>&1 &
SENDER2_PID=$!

echo "演示运行中... (等待15秒)"
sleep 15

# 停止所有进程
echo "停止演示..."
kill $SENDER1_PID $SENDER2_PID $ROUTER_PID $RECEIVER_PID 2>/dev/null
wait $SENDER1_PID $SENDER2_PID $ROUTER_PID $RECEIVER_PID 2>/dev/null

# 检查结果
echo ""
echo "=========================================="
echo "3. 检查演示结果"
echo "=========================================="

if [ -f "results/demo/demo_received.log" ]; then
    lines=$(wc -l < results/demo/demo_received.log)
    if [ $lines -gt 1 ]; then
        echo "✓ 演示成功！接收到 $((lines-1)) 条数据记录"
        
        # 显示简单统计
        echo ""
        echo "数据统计:"
        python3 -c "
import pandas as pd
try:
    df = pd.read_csv('results/demo/demo_received.log')
    print(f'  Flow 1: {len(df[df[\"flow_id\"]==1])} 个包')
    print(f'  Flow 2: {len(df[df[\"flow_id\"]==2])} 个包')
    total_bytes = df['packet_size'].sum()
    print(f'  总数据: {total_bytes} 字节 ({total_bytes/1024:.1f} KB)')
except Exception as e:
    print(f'  统计失败: {e}')
"
    else
        echo "⚠️  演示完成但数据较少"
    fi
else
    echo "❌ 演示失败 - 未找到接收数据"
fi

echo ""
echo "=========================================="
echo "4. 生成简单图表"
echo "=========================================="

# 生成简单的图表
python3 -c "
import matplotlib.pyplot as plt
import pandas as pd
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Songti SC']
plt.rcParams['axes.unicode_minus'] = False

try:
    # 读取数据
    df = pd.read_csv('results/demo/demo_received.log')
    
    # 按流分组
    flow1_data = df[df['flow_id'] == 1]
    flow2_data = df[df['flow_id'] == 2]
    
    # 创建图表
    plt.figure(figsize=(10, 6))
    
    # 计算累计字节数
    if len(flow1_data) > 0:
        flow1_cumsum = flow1_data['packet_size'].cumsum()
        plt.plot(range(len(flow1_cumsum)), flow1_cumsum/1024, 
                label='Flow 1 (权重=1)', linewidth=2, marker='o', markersize=3)
    
    if len(flow2_data) > 0:
        flow2_cumsum = flow2_data['packet_size'].cumsum()
        plt.plot(range(len(flow2_cumsum)), flow2_cumsum/1024, 
                label='Flow 2 (权重=2)', linewidth=2, marker='s', markersize=3)
    
    plt.xlabel('数据包序号')
    plt.ylabel('累计接收数据 (KB)')
    plt.title('WFQ演示 - 累计吞吐量')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('results/demo/demo_chart.png', dpi=150, bbox_inches='tight')
    print('✓ 图表已保存到 results/demo/demo_chart.png')
    
except Exception as e:
    print(f'图表生成失败: {e}')
" 2>/dev/null

# 移动延迟文件到demo目录
if [ -f "results/delays_flow_1.csv" ]; then
    mv results/delays_flow_1.csv results/demo/
fi
if [ -f "results/delays_flow_2.csv" ]; then
    mv results/delays_flow_2.csv results/demo/
fi

echo ""
echo "=================================================="
echo "               演示完成！"
echo "=================================================="
echo ""
echo "生成的文件 (位于 results/demo/ 目录):"
echo "  📊 demo_chart.png           - 演示图表"
echo "  📝 demo_received.log        - 接收数据"
echo "  📋 demo_*.log               - 组件日志"
echo "  ⏱️  delays_flow_*.csv       - 延迟数据 (echo模式)"
echo ""
echo "下一步可以运行完整实验:"
echo "  ./scripts/run_all_experiments.sh"
echo ""
echo "或单独运行FIFO/WFQ实验:"
echo "  ./scripts/run_fifo_experiment.sh"
echo "  ./scripts/run_wfq_experiment.sh"
echo ""
echo "查看详细文档:"
echo "  cat README.md"
echo "  cat docs/design_report.md"
echo "=================================================="

echo "演示脚本执行完成 ✨"
echo ""
echo "💡 注意：演示使用echo模式，可以测量真实的端到端延迟"
echo "   完整实验使用stats模式，专注于吞吐量对比分析"
