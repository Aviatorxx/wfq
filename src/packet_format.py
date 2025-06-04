"""
数据包格式定义模块
定义项目使用的数据包结构和相关工具函数
"""

import struct
import socket
import time

class ProjectPacket:
    """项目数据包类，处理24字节项目头 + 数据负载"""
    
    # 项目头格式：源IP(4) + 目标IP(4) + 源端口(2) + 目标端口(2) + 权重(4) + 流ID(4) + 序列号(4) = 24字节
    HEADER_FORMAT = '!IIHHI II'  # 网络字节序
    HEADER_SIZE = 24
    MAX_DATA_SIZE = 1400
    MAX_PACKET_SIZE = HEADER_SIZE + MAX_DATA_SIZE
    
    def __init__(self, src_ip="127.0.0.1", dst_ip="127.0.0.1", 
                 src_port=0, dst_port=0, weight=1, flow_id=1, seq_num=0, data=b''):
        self.src_ip = self._ip_to_int(src_ip)
        self.dst_ip = self._ip_to_int(dst_ip)  
        self.src_port = src_port
        self.dst_port = dst_port
        self.weight = weight
        self.flow_id = flow_id
        self.seq_num = seq_num
        self.data = data[:self.MAX_DATA_SIZE]  # 限制数据大小
        self.timestamp = time.time()  # 添加时间戳用于延迟计算
        
    @staticmethod
    def _ip_to_int(ip_str):
        """将IP字符串转换为32位整数"""
        return struct.unpack("!I", socket.inet_aton(ip_str))[0]
        
    @staticmethod  
    def _int_to_ip(ip_int):
        """将32位整数转换为IP字符串"""
        return socket.inet_ntoa(struct.pack("!I", ip_int))
        
    def pack(self):
        """将数据包打包为字节序列"""
        header = struct.pack(self.HEADER_FORMAT,
                           self.src_ip, self.dst_ip,
                           self.src_port, self.dst_port, 
                           self.weight, self.flow_id, self.seq_num)
        return header + self.data
        
    @classmethod
    def unpack(cls, packet_bytes):
        """从字节序列解包数据包"""
        if len(packet_bytes) < cls.HEADER_SIZE:
            raise ValueError("数据包长度不足")
            
        header = packet_bytes[:cls.HEADER_SIZE]
        data = packet_bytes[cls.HEADER_SIZE:]
        
        unpacked = struct.unpack(cls.HEADER_FORMAT, header)
        src_ip, dst_ip, src_port, dst_port, weight, flow_id, seq_num = unpacked
        
        packet = cls(
            src_ip=cls._int_to_ip(src_ip),
            dst_ip=cls._int_to_ip(dst_ip),
            src_port=src_port,
            dst_port=dst_port,
            weight=weight,
            flow_id=flow_id,
            seq_num=seq_num,
            data=data
        )
        return packet
        
    def get_size(self):
        """获取数据包总大小"""
        return self.HEADER_SIZE + len(self.data)
        
    def __str__(self):
        return (f"Packet(flow={self.flow_id}, seq={self.seq_num}, "
                f"weight={self.weight}, size={self.get_size()}, "
                f"src={self._int_to_ip(self.src_ip)}:{self.src_port}, "
                f"dst={self._int_to_ip(self.dst_ip)}:{self.dst_port})")

# 测试代码
if __name__ == "__main__":
    # 创建测试数据包
    test_data = b"Hello WFQ!" * 10  # 创建一些测试数据
    packet = ProjectPacket(
        src_ip="192.168.1.1",
        dst_ip="192.168.1.2", 
        src_port=12345,
        dst_port=8080,
        weight=2,
        flow_id=1,
        seq_num=100,
        data=test_data
    )
    
    print("原始数据包:")
    print(packet)
    
    # 打包和解包测试
    packed_data = packet.pack()
    print(f"\n打包后大小: {len(packed_data)} 字节")
    
    unpacked_packet = ProjectPacket.unpack(packed_data)
    print("\n解包后数据包:")
    print(unpacked_packet)
    print(f"数据内容: {unpacked_packet.data}")
