import os
import socket
import struct

from scripts.train_infer import train_infer

class UnixSocketServer:
    def __init__(self, socket_path, train_infer_func):
        self.socket_path = socket_path
        self.train_infer_func= train_infer_func
        self.pathstatus_format = '10Q'
        self.pathstatus_size = struct.calcsize(self.pathstatus_format)
    
    def start(self):
        # 启动服务器
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(self.socket_path)
            server.listen()
            print(f"[Socket server started] Listening at {self.socket_path}")

            while True:
                conn, _ = server.accept()
                with conn:
                    self.handle_connection(conn)

    def handle_connection(self, conn):
        num_paths_data = conn.recv(4)
        num_paths = struct.unpack('<I', num_paths_data)[0]

        path_status = []
        for _ in range(num_paths):
            data = conn.recv(self.pathstatus_size)
            ps = struct.unpack(self.pathstatus_format, data)
            path_status.append({
                'PathID': ps[0],
                'SRTT': ps[1],
                'CWND': ps[2],
                'QueueSize': ps[3],
                'Send': ps[4],
                'Retrans': ps[5],
                'Lost': ps[6],
                'Received': ps[7],
                'PacketSize': ps[8],
                'FileComplete': ps[9]
            })

        # 调用推理方法，返回动作
        selected_path_id = self.train_infer_func(path_status)
        conn.sendall(struct.pack('Q', selected_path_id))
