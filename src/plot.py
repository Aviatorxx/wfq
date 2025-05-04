import pandas as pd, matplotlib.pyplot as plt, argparse

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

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="logs/recv_log_fifo.csv or logs/send_log_fifo.csv")
    ap.add_argument("--title", default="FIFO累积字节")
    ap.add_argument("--type", choices=["bytes", "rtt"], default="bytes", 
                    help="图表类型: bytes表示累积字节, rtt表示延迟")
    args = ap.parse_args()
    
    if args.type == "bytes":
        plot_bytes(args.csv, args.title)
    else:
        plot_rtt(args.csv, args.title)
