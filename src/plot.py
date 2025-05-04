import pandas as pd, matplotlib.pyplot as plt, argparse, numpy as np

# 设置中文字体
plt.rc('font', family='Songti SC', size=13)

def plot_bytes(csv_path, title):
    df = pd.read_csv(csv_path)
    df['ts'] = (df['us'] - df['us'].min())/1e6  # 秒
    df['bytes_cum'] = df.groupby('flow')['size'].cumsum()
    for flow, sub in df.groupby('flow'):
        plt.plot(sub['ts'], sub['bytes_cum'], label=f"流 {flow}")
    plt.xlabel("时间 (秒)")
    plt.ylabel("累积字节数")
    plt.title(title)
    plt.legend(); plt.show()
    
def plot_rtt(csv_path, title):
    df = pd.read_csv(csv_path)
    df['ts'] = (df['us'] - df['us'].min())/1e6  # 秒
    for flow, sub in df.groupby('flow'):
        plt.scatter(sub['ts'], sub['rtt_us']/1000, label=f"流 {flow}", alpha=0.7, s=10)
    plt.xlabel("时间 (秒)")
    plt.ylabel("RTT (毫秒)")
    plt.title(title)
    plt.legend(); plt.show()

def plot_bytes_and_rate(csv_path, title):
    df = pd.read_csv(csv_path)
    df['ts'] = (df['us'] - df['us'].min())/1e6  # 秒
    df['bytes_cum'] = df.groupby('flow')['size'].cumsum()
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 8), gridspec_kw={'height_ratios': [2, 1]})

    # 累积字节数
    for flow, sub in df.groupby('flow'):
        ax1.plot(sub['ts'], sub['bytes_cum'], label=f"流 {flow}")
    ax1.set_ylabel("累积字节数")
    ax1.set_title(title)
    ax1.legend()

    # 瞬时带宽（滑动窗口1秒）
    window = 1  # 秒
    for flow, sub in df.groupby('flow'):
        sub = sub.sort_values('ts')
        ts = sub['ts'].values
        sizes = sub['size'].values
        rate = []
        t_points = np.arange(ts[0], ts[-1], 0.1)
        for t in t_points:
            mask = (ts >= t - window) & (ts < t)
            rate.append(sizes[mask].sum() / window if mask.any() else 0)
        ax2.plot(t_points, rate, label=f"流 {flow}")
    ax2.set_xlabel("时间 (秒)")
    ax2.set_ylabel("带宽 (字节/秒)")
    ax2.legend()
    ax2.set_title("瞬时带宽（滑动窗口1秒）")

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="logs/recv_log_fifo.csv or logs/send_log_fifo.csv")
    ap.add_argument("--title", default="FIFO累积字节")
    ap.add_argument("--type", choices=["bytes", "rtt", "bytes_rate"], default="bytes", 
                    help="图表类型: bytes表示累积字节, rtt表示延迟, bytes_rate表示累积字节+瞬时带宽")
    args = ap.parse_args()
    
    if args.type == "bytes":
        plot_bytes(args.csv, args.title)
    elif args.type == "rtt":
        plot_rtt(args.csv, args.title)
    elif args.type == "bytes_rate":
        plot_bytes_and_rate(args.csv, args.title)
