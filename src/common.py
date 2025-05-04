import struct, time, json, csv

PROJECT_HDR_FMT = "!4s4sHHHH"   # IPv4(4)+IPv4(4)+port+port+weight+flowid = 16B
PROJECT_HDR_LEN = struct.calcsize(PROJECT_HDR_FMT)  # 16

def make_header(src_ip, dst_ip, sport, dport, weight, flow_id):
    return struct.pack(PROJECT_HDR_FMT,
                       src_ip, dst_ip, sport, dport, weight, flow_id)

def parse_header(data: bytes):
    return struct.unpack(PROJECT_HDR_FMT, data[:PROJECT_HDR_LEN])

def now_us() -> int:
    return int(time.time()*1e6)

def log_csv(path: str, row: dict):
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, row.keys())
        if f.tell() == 0: w.writeheader()
        w.writerow(row)
