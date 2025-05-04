#!/usr/bin/env python3
import subprocess
import time
import os
import signal
import sys
import atexit

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 清理旧的日志文件
for f in os.listdir("logs"):
    if f.endswith(".csv"):
        os.remove(os.path.join("logs", f))

# 保存所有子进程以便在退出时清理
child_processes = []

def cleanup_processes():
    """清理所有子进程"""
    print("\n清理所有子进程...")
    for p in child_processes:
        try:
            if p.poll() is None:  # 如果进程还在运行
                p.terminate()
                p.wait(timeout=2)
        except Exception as e:
            print(f"清理进程时出错: {e}")

# 注册退出处理函数
atexit.register(cleanup_processes)

def run_experiment(router_type="fifo"):
    print(f"\n开始 {router_type.upper()} 路由器实验...")
    
    # 启动接收器 (echo模式)
    print("启动接收器...")
    try:
        receiver = subprocess.Popen(
            ["python3", "src/receiver.py", "--mode", "echo", "--router", router_type],
            cwd="./"
        )
        child_processes.append(receiver)
        time.sleep(1)  # 等待接收器启动
    except Exception as e:
        print(f"启动接收器失败: {e}")
        return False
    
    # 启动路由器
    print(f"启动 {router_type} 路由器...")
    try:
        if router_type == "fifo":
            router = subprocess.Popen(["python3", "src/router.py"], cwd="./")
        elif router_type == "rr":
            router = subprocess.Popen(["python3", "src/router_rr.py"], cwd="./")
        elif router_type == "wfq":
            router = subprocess.Popen(["python3", "src/router_wfq.py"], cwd="./")
        else:
            print(f"未知的路由器类型: {router_type}")
            receiver.terminate()
            return False
            
        child_processes.append(router)
        time.sleep(1)  # 等待路由器启动
    except Exception as e:
        print(f"启动路由器失败: {e}")
        receiver.terminate()
        return False
    
    # 启动第一个发送器 (flow_id=1, weight=1, size=1024)
    print("启动发送器 1 (flow_id=1, weight=1, size=1024)...")
    try:
        sender1 = subprocess.Popen(
            ["python3", "src/sender.py", "--flow", "1", "--weight", "1", "--size", "1024", "--mode", router_type],
            cwd="./"
        )
        child_processes.append(sender1)
    except Exception as e:
        print(f"启动发送器1失败: {e}")
        router.terminate()
        receiver.terminate()
        return False
    
    # 等待2秒
    time.sleep(2)
    
    # 启动第二个发送器 (flow_id=2, weight=1, size=512)
    print("启动发送器 2 (flow_id=2, weight=1, size=512)...")
    try:
        sender2 = subprocess.Popen(
            ["python3", "src/sender.py", "--flow", "2", "--weight", "1", "--size", "512", "--mode", router_type],
            cwd="./"
        )
        child_processes.append(sender2)
    except Exception as e:
        print(f"启动发送器2失败: {e}")
        # 继续实验，不中断
    
    # 等待2秒
    time.sleep(2)
    
    # 启动第三个发送器 (flow_id=3, weight=2, size=1024)
    print("启动发送器 3 (flow_id=3, weight=2, size=1024)...")
    try:
        sender3 = subprocess.Popen(
            ["python3", "src/sender.py", "--flow", "3", "--weight", "2", "--size", "1024", "--mode", router_type],
            cwd="./"
        )
        child_processes.append(sender3)
    except Exception as e:
        print(f"启动发送器3失败: {e}")
        # 继续实验，不中断
    
    # 等待2秒
    time.sleep(2)
    
    # 停止第二个发送器
    print("停止发送器 2...")
    try:
        sender2.terminate()
        sender2.wait(timeout=2)
    except Exception as e:
        print(f"停止发送器2失败: {e}")
    
    # 等待2秒
    time.sleep(2)
    
    # 停止所有进程
    print("停止所有进程...")
    try:
        sender1.terminate()
        sender3.terminate()
        router.terminate()
        receiver.terminate()
        
        # 等待所有进程结束，设置超时
        sender1.wait(timeout=2)
        sender3.wait(timeout=2)
        router.wait(timeout=2)
        receiver.wait(timeout=2)
    except Exception as e:
        print(f"停止进程时出错: {e}")
    
    print(f"{router_type.upper()} 实验完成!")
    
    # 生成图表
    try:
        print(f"生成{router_type.upper()}累积字节图...")
        subprocess.run(["python3", "src/plot.py", f"logs/recv_log_{router_type}.csv", "--title", f"{router_type.upper()} cumulative bytes", "--type", "bytes"])
        
        print(f"生成{router_type.upper()}RTT延迟图...")
        subprocess.run(["python3", "src/plot.py", f"logs/send_log_{router_type}.csv", "--title", f"{router_type.upper()} packet delay", "--type", "rtt"])
    except Exception as e:
        print(f"生成图表失败: {e}")
    
    return True

if __name__ == "__main__":
    try:
        # 解析命令行参数
        import argparse
        parser = argparse.ArgumentParser(description="运行网络调度实验")
        parser.add_argument("--mode", choices=["all", "fifo", "rr", "wfq"], default="all", 
                          help="实验模式: all=所有实验, fifo=FIFO实验, rr=RR实验, wfq=WFQ实验")
        args = parser.parse_args()
        
        success_count = 0
        total_count = 0
        
        # 根据命令行参数运行相应的实验
        if args.mode in ["all", "fifo"]:
            total_count += 1
            print("\n运行FIFO实验...")
            fifo_success = run_experiment("fifo")
            if fifo_success:
                success_count += 1
            # 等待一段时间确保所有进程都已结束
            time.sleep(2)
        
        if args.mode in ["all", "rr"]:
            total_count += 1
            print("\n运行RR实验...")
            rr_success = run_experiment("rr")
            if rr_success:
                success_count += 1
            # 等待一段时间确保所有进程都已结束
            time.sleep(2)
        
        if args.mode in ["all", "wfq"]:
            total_count += 1
            print("\n运行WFQ实验...")
            wfq_success = run_experiment("wfq")
            if wfq_success:
                success_count += 1
        
        print(f"\n所有实验完成! 成功: {success_count}/{total_count}")
        print("日志文件保存在 logs/ 目录下")
        
    except KeyboardInterrupt:
        print("\n实验被用户中断")
        cleanup_processes()
        sys.exit(1)
    except Exception as e:
        print(f"\n实验过程中出错: {e}")
        cleanup_processes()
        sys.exit(1)