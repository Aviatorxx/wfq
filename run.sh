#!/bin/bash

# WFQ项目启动脚本
# 提供简单的脚本选择界面

echo "=================================================="
echo "       WFQ网络调度算法项目"
echo "=================================================="
echo ""

# 设置所有脚本为可执行
chmod +x scripts/*.sh 2>/dev/null

echo "请选择要运行的实验："
echo ""
echo "1. 快速演示 (20秒) - Echo模式基本功能演示"
echo "   ./scripts/demo.sh"
echo ""
echo "2. Stats模式演示 (60秒) - 纯吞吐量分析"  
echo "   ./scripts/stats_demo.sh"
echo ""
echo "3. 完整对比实验 (5分钟) - FIFO vs WFQ完整分析"
echo "   ./scripts/full_comparison.sh"
echo ""
echo "4. 单独FIFO实验"
echo "   ./scripts/run_fifo_experiment.sh"
echo ""
echo "5. 单独WFQ实验"
echo "   ./scripts/run_wfq_experiment.sh"
echo ""
echo "6. 组件测试"
echo "   ./scripts/test_components.sh"
echo ""
echo "=================================================="
echo "推荐运行顺序："
echo "  第一次使用: 1 → 2 → 3"
echo "  课程演示: 1 → 3"
echo "  快速验证: 1"
echo "=================================================="
echo ""

# 如果提供了参数，直接运行对应脚本
case "$1" in
    "1"|"demo")
        echo "🚀 运行快速演示..."
        ./scripts/demo.sh
        ;;
    "2"|"stats")
        echo "🚀 运行Stats模式演示..."
        ./scripts/stats_demo.sh
        ;;
    "3"|"full"|"comparison")
        echo "🚀 运行完整对比实验..."
        ./scripts/full_comparison.sh
        ;;
    "4"|"fifo")
        echo "🚀 运行FIFO实验..."
        ./scripts/run_fifo_experiment.sh
        ;;
    "5"|"wfq")
        echo "🚀 运行WFQ实验..."
        ./scripts/run_wfq_experiment.sh
        ;;
    "6"|"test")
        echo "🚀 运行组件测试..."
        ./scripts/test_components.sh
        ;;
    *)
        echo "💡 使用方法:"
        echo "  ./run.sh [选项]"
        echo ""
        echo "选项:"
        echo "  1 或 demo        - 快速演示"
        echo "  2 或 stats       - Stats模式演示"
        echo "  3 或 full        - 完整对比实验"
        echo "  4 或 fifo        - FIFO实验"
        echo "  5 或 wfq         - WFQ实验"
        echo "  6 或 test        - 组件测试"
        echo ""
        echo "示例:"
        echo "  ./run.sh demo      # 运行快速演示"
        echo "  ./run.sh full      # 运行完整实验"
        ;;
esac
