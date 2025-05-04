import pandas as pd, matplotlib.pyplot as plt, argparse

def plot_bytes(csv_path, title):
    df = pd.read_csv(csv_path)
    df['ts'] = (df['us'] - df['us'].min())/1e6  # 秒
    df['bytes_cum'] = df.groupby('flow')['size'].cumsum()
    for flow, sub in df.groupby('flow'):
        plt.plot(sub['ts'], sub['bytes_cum'], label=f"flow {flow}")
    plt.xlabel("Time (s)")
    plt.ylabel("Cumulative Bytes")
    plt.title(title)
    plt.legend(); plt.show()
    
def plot_rtt(csv_path, title):
    df = pd.read_csv(csv_path)
    df['ts'] = (df['us'] - df['us'].min())/1e6  # 秒
    for flow, sub in df.groupby('flow'):
        plt.scatter(sub['ts'], sub['rtt_us']/1000, label=f"flow {flow}", alpha=0.7, s=10)
    plt.xlabel("Time (s)")
    plt.ylabel("RTT (ms)")
    plt.title(title)
    plt.legend(); plt.show()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="logs/recv_log_fifo.csv or logs/send_log_fifo.csv")
    ap.add_argument("--title", default="FIFO cumulative bytes")
    ap.add_argument("--type", choices=["bytes", "rtt"], default="bytes", 
                    help="Plot type: bytes for cumulative bytes, rtt for delay")
    args = ap.parse_args()
    
    if args.type == "bytes":
        plot_bytes(args.csv, args.title)
    else:
        plot_rtt(args.csv, args.title)
