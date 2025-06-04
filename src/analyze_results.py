#!/usr/bin/env python3
"""
分析实验结果并生成图表 - 修正版
支持--output-dir参数，确保图表输出到正确目录
"""

import argparse
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import pandas as pd

# 添加src目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置matplotlib字体（适配Mac系统）
plt.rcParams['font.sans-serif'] = ['Songti SC', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def read_throughput_data(data_file):
    """读取接收数据，计算吞吐量"""
    flow_data = defaultdict(list)
    
    if not os.path.exists(data_file):
        print(f"数据文件不存在: {data_file}")
        return flow_data
        
    try:
        with open(data_file, 'r') as f:
            header = f.readline().strip()  # 跳过标题行
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    timestamp = float(parts[0])
                    flow_id = int(parts[1])
                    packet_size = int(parts[2])
                    flow_data[flow_id].append((timestamp, packet_size))
    except Exception as e:
        print(f"读取数据文件失败: {e}")
        
    return flow_data

def read_delay_data(delay_files):
    """读取延迟数据"""
    flow_delays = defaultdict(list)
    
    for flow_id, delay_file in delay_files.items():
        if os.path.exists(delay_file):
            try:
                with open(delay_file, 'r') as f:
                    f.readline()  # 跳过标题行
                    for line in f:
                        parts = line.strip().split(',')
                        if len(parts) >= 5:
                            timestamp = float(parts[0])
                            delay = float(parts[4])
                            if delay > 0:  # 只包含有效的延迟数据
                                flow_delays[flow_id].append((timestamp, delay))
            except Exception as e:
                print(f"读取延迟文件 {delay_file} 失败: {e}")
                
    return flow_delays

def plot_throughput(flow_data, output_file, title):
    """绘制吞吐量图"""
    plt.figure(figsize=(12, 8))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    line_styles = ['-', '--', '-.', ':', '-']
    
    for i, flow_id in enumerate(sorted(flow_data.keys())):
        data = flow_data[flow_id]
        if not data:
            continue
            
        data.sort(key=lambda x: x[0])
        
        timestamps = []
        cumulative_bytes = []
        total_bytes = 0
        
        for timestamp, packet_size in data:
            total_bytes += packet_size
            timestamps.append(timestamp)
            cumulative_bytes.append(total_bytes)
        
        color = colors[i % len(colors)]
        line_style = line_styles[i % len(line_styles)]
        
        plt.plot(timestamps, [b/1024 for b in cumulative_bytes], 
                label=f'Flow {flow_id}', 
                color=color, 
                linestyle=line_style,
                linewidth=2, 
                marker='o', 
                markersize=3,
                markevery=max(1, len(timestamps)//20))
    
    plt.xlabel('时间 (秒)', fontsize=12)
    plt.ylabel('累计接收字节数 (KB)', fontsize=12)
    plt.title(title + ' - 累计吞吐量', fontsize=14, fontweight='bold')
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 创建输出目录
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 吞吐量图已保存: {output_file}")

def plot_delays(flow_delays, output_file, title):
    """绘制延迟图"""
    if not flow_delays or all(len(delays) == 0 for delays in flow_delays.values()):
        print(f"❌ 没有有效的延迟数据，跳过延迟图生成: {output_file}")
        return
        
    plt.figure(figsize=(12, 8))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    # 创建子图：散点图和箱形图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 子图1: 时间 vs 延迟 散点图
    for i, flow_id in enumerate(sorted(flow_delays.keys())):
        delays = flow_delays[flow_id]
        if not delays:
            continue
            
        delays.sort(key=lambda x: x[0])
        
        timestamps = [d[0] for d in delays]
        delay_values = [d[1] for d in delays]
        
        if timestamps:
            start_time = min(timestamps)
            timestamps = [t - start_time for t in timestamps]
        
        color = colors[i % len(colors)]
        
        ax1.scatter(timestamps, delay_values, 
                   label=f'Flow {flow_id}', 
                   color=color, 
                   alpha=0.6, 
                   s=20)
    
    ax1.set_xlabel('时间 (秒)', fontsize=12)
    ax1.set_ylabel('包延迟 (毫秒)', fontsize=12)
    ax1.set_title(f'{title} - 延迟随时间变化', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 子图2: 延迟分布箱形图
    delay_data = []
    flow_labels = []
    
    for flow_id in sorted(flow_delays.keys()):
        delays = flow_delays[flow_id]
        if delays:
            delay_values = [d[1] for d in delays]
            delay_data.append(delay_values)
            flow_labels.append(f'Flow {flow_id}')
    
    if delay_data:
        box_plot = ax2.boxplot(delay_data, labels=flow_labels, patch_artist=True)
        
        for i, patch in enumerate(box_plot['boxes']):
            patch.set_facecolor(colors[i % len(colors)])
            patch.set_alpha(0.7)
    
    ax2.set_xlabel('流ID', fontsize=12)
    ax2.set_ylabel('包延迟 (毫秒)', fontsize=12)
    ax2.set_title(f'{title} - 延迟分布对比', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # 创建输出目录
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 延迟图已保存: {output_file}")

def generate_comparison_plots(data_dir, output_dir=None):
    """生成FIFO vs WFQ对比图"""
    
    # 读取数据
    fifo_data = read_throughput_data(f'{data_dir}/fifo_received_data.log')
    wfq_data = read_throughput_data(f'{data_dir}/wfq_received_data.log')
    
    # 读取延迟数据
    fifo_delay_files = {}
    wfq_delay_files = {}
    
    for flow_id in [1, 2, 3]:
        fifo_delay_file = f'{data_dir}/fifo_delays_flow_{flow_id}.csv'
        wfq_delay_file = f'{data_dir}/wfq_delays_flow_{flow_id}.csv'
        
        if os.path.exists(fifo_delay_file):
            fifo_delay_files[flow_id] = fifo_delay_file
        if os.path.exists(wfq_delay_file):
            wfq_delay_files[flow_id] = wfq_delay_file
    
    fifo_delays = read_delay_data(fifo_delay_files)
    wfq_delays = read_delay_data(wfq_delay_files)
    
    if not fifo_data and not wfq_data:
        print("❌ 没有找到实验数据，请先运行实验")
        return
    
    # 生成6子图对比图
    plt.figure(figsize=(16, 12))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # 子图1：FIFO吞吐量
    plt.subplot(2, 3, 1)
    for i, flow_id in enumerate(sorted(fifo_data.keys())):
        data = fifo_data[flow_id]
        if data:
            data.sort(key=lambda x: x[0])
            timestamps = [d[0] for d in data]
            cumulative_bytes = []
            total = 0
            for _, size in data:
                total += size
                cumulative_bytes.append(total)
            plt.plot(timestamps, [b/1024 for b in cumulative_bytes], 
                    label=f'Flow {flow_id}', color=colors[i % len(colors)], linewidth=2)
    plt.title('FIFO调度算法 - 吞吐量', fontsize=12, fontweight='bold')
    plt.xlabel('时间 (秒)')
    plt.ylabel('累计接收 (KB)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图2：WFQ吞吐量
    plt.subplot(2, 3, 2)
    for i, flow_id in enumerate(sorted(wfq_data.keys())):
        data = wfq_data[flow_id]
        if data:
            data.sort(key=lambda x: x[0])
            timestamps = [d[0] for d in data]
            cumulative_bytes = []
            total = 0
            for _, size in data:
                total += size
                cumulative_bytes.append(total)
            plt.plot(timestamps, [b/1024 for b in cumulative_bytes], 
                    label=f'Flow {flow_id}', color=colors[i % len(colors)], linewidth=2)
    plt.title('WFQ调度算法 - 吞吐量', fontsize=12, fontweight='bold')
    plt.xlabel('时间 (秒)')
    plt.ylabel('累计接收 (KB)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 总吞吐量对比
    plt.subplot(2, 3, 3)
    fifo_totals = {}
    wfq_totals = {}
    
    for flow_id in sorted(set(list(fifo_data.keys()) + list(wfq_data.keys()))):
        fifo_total = sum(size for _, size in fifo_data.get(flow_id, []))
        wfq_total = sum(size for _, size in wfq_data.get(flow_id, []))
        fifo_totals[flow_id] = fifo_total / 1024
        wfq_totals[flow_id] = wfq_total / 1024
    
    flows = sorted(fifo_totals.keys())
    x = np.arange(len(flows))
    width = 0.35
    
    plt.bar(x - width/2, [fifo_totals.get(f, 0) for f in flows], 
            width, label='FIFO', alpha=0.8, color='#1f77b4')
    plt.bar(x + width/2, [wfq_totals.get(f, 0) for f in flows], 
            width, label='WFQ', alpha=0.8, color='#ff7f0e')
    
    plt.title('总吞吐量对比', fontsize=12, fontweight='bold')
    plt.xlabel('流ID')
    plt.ylabel('总接收数据 (KB)')
    plt.xticks(x, [f'Flow {f}' for f in flows])
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    
    # 延迟分布对比
    if fifo_delays or wfq_delays:
        # FIFO延迟
        plt.subplot(2, 3, 4)
        if fifo_delays:
            delay_data = []
            flow_labels = []
            for flow_id in sorted(fifo_delays.keys()):
                delays = fifo_delays[flow_id]
                if delays:
                    delay_values = [d[1] for d in delays]
                    delay_data.append(delay_values)
                    flow_labels.append(f'Flow {flow_id}')
            
            if delay_data:
                box_plot = plt.boxplot(delay_data, labels=flow_labels, patch_artist=True)
                for i, patch in enumerate(box_plot['boxes']):
                    patch.set_facecolor(colors[i % len(colors)])
                    patch.set_alpha(0.7)
        
        plt.title('FIFO - 延迟分布', fontsize=12, fontweight='bold')
        plt.xlabel('流ID')
        plt.ylabel('延迟 (ms)')
        plt.grid(True, alpha=0.3, axis='y')
        
        # WFQ延迟
        plt.subplot(2, 3, 5)
        if wfq_delays:
            delay_data = []
            flow_labels = []
            for flow_id in sorted(wfq_delays.keys()):
                delays = wfq_delays[flow_id]
                if delays:
                    delay_values = [d[1] for d in delays]
                    delay_data.append(delay_values)
                    flow_labels.append(f'Flow {flow_id}')
            
            if delay_data:
                box_plot = plt.boxplot(delay_data, labels=flow_labels, patch_artist=True)
                for i, patch in enumerate(box_plot['boxes']):
                    patch.set_facecolor(colors[i % len(colors)])
                    patch.set_alpha(0.7)
        
        plt.title('WFQ - 延迟分布', fontsize=12, fontweight='bold')
        plt.xlabel('流ID')
        plt.ylabel('延迟 (ms)')
        plt.grid(True, alpha=0.3, axis='y')
        
        # 平均延迟对比
        plt.subplot(2, 3, 6)
        fifo_avg_delays = {}
        wfq_avg_delays = {}
        
        for flow_id in flows:
            if flow_id in fifo_delays and fifo_delays[flow_id]:
                fifo_avg_delays[flow_id] = np.mean([d[1] for d in fifo_delays[flow_id]])
            if flow_id in wfq_delays and wfq_delays[flow_id]:
                wfq_avg_delays[flow_id] = np.mean([d[1] for d in wfq_delays[flow_id]])
        
        if fifo_avg_delays or wfq_avg_delays:
            x = np.arange(len(flows))
            width = 0.35
            
            plt.bar(x - width/2, [fifo_avg_delays.get(f, 0) for f in flows], 
                    width, label='FIFO', alpha=0.8, color='#1f77b4')
            plt.bar(x + width/2, [wfq_avg_delays.get(f, 0) for f in flows], 
                    width, label='WFQ', alpha=0.8, color='#ff7f0e')
            
            plt.title('平均延迟对比', fontsize=12, fontweight='bold')
            plt.xlabel('流ID')
            plt.ylabel('平均延迟 (ms)')
            plt.xticks(x, [f'Flow {f}' for f in flows])
            plt.legend()
            plt.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # 保存对比图
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        comparison_file = f'{output_dir}/algorithm_comparison.png'
    else:
        comparison_file = f'{data_dir}/algorithm_comparison.png'
    
    plt.savefig(comparison_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ 算法对比图已保存: {comparison_file}")

def main():
    parser = argparse.ArgumentParser(description='分析WFQ实验结果 - 修正版')
    parser.add_argument('--algorithm', choices=['fifo', 'wfq'], 
                       help='分析的算法类型')
    parser.add_argument('--data-file', help='接收数据文件路径')
    parser.add_argument('--generate-comparison', action='store_true',
                       help='生成算法对比图')
    parser.add_argument('--experiments-dir', default='.',
                       help='实验数据目录')
    parser.add_argument('--output-dir', help='图表输出目录')
    
    args = parser.parse_args()
    
    # 生成对比图
    if args.generate_comparison:
        generate_comparison_plots(args.experiments_dir, args.output_dir)
        return
    
    # 生成单个算法图表
    if not args.algorithm or not args.data_file:
        print("请指定算法类型和数据文件，或使用 --generate-comparison 生成对比图")
        return
    
    # 确定数据文件路径
    if not os.path.isabs(args.data_file):
        data_file = os.path.join(args.experiments_dir, args.data_file)
    else:
        data_file = args.data_file
    
    # 确定延迟文件的基础目录
    data_dir = os.path.dirname(data_file)
    
    # 确定输出目录
    if args.output_dir:
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = data_dir
    
    # 读取吞吐量数据
    flow_data = read_throughput_data(data_file)
    
    if flow_data:
        # 生成吞吐量图
        output_file = f'{output_dir}/{args.algorithm}_throughput.png'
        title = f'{args.algorithm.upper()}调度算法'
        plot_throughput(flow_data, output_file, title)
    
    # 读取延迟数据
    delay_files = {}
    for flow_id in [1, 2, 3]:
        delay_file = f'{data_dir}/{args.algorithm}_delays_flow_{flow_id}.csv'
        if os.path.exists(delay_file):
            delay_files[flow_id] = delay_file
    
    if delay_files:
        flow_delays = read_delay_data(delay_files)
        if flow_delays:
            # 生成延迟图
            output_file = f'{output_dir}/{args.algorithm}_delays.png'
            title = f'{args.algorithm.upper()}调度算法'
            plot_delays(flow_delays, output_file, title)
        else:
            print(f"⚠️  延迟文件存在但没有有效数据: {list(delay_files.values())}")
    else:
        print(f"⚠️  没有找到延迟文件: {data_dir}/{args.algorithm}_delays_flow_*.csv")
    
    print(f"✅ {args.algorithm.upper()}实验分析完成")

if __name__ == '__main__':
    main()