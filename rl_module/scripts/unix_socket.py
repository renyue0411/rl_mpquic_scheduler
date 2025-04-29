import os
import socket
import struct

from scripts.train_infer import train_infer
from a2c.utils import SOCKET_PATH

class UnixSocketServer:
    def __init__(self, module_mode, socket_path=SOCKET_PATH):
        self.socket_path = socket_path
        self.module_mode = module_mode
        self.path_status = []
        self.pathstatus_format = '10Q'
        self.pathstatus_size = struct.calcsize(self.pathstatus_format)
    
    def start(self):
        # run UNIX socket sever
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(self.socket_path)
            server.listen()
            print(f"[Unix socket] Listening at {self.socket_path}")

            while True:
                conn, _ = server.accept()
                with conn:
                    self.handle_connection(conn)

    def handle_connection(self, conn):
        num_paths_data = conn.recv(4)
        num_paths = struct.unpack('<I', num_paths_data)[0]

        for _ in range(num_paths):
            data = conn.recv(self.pathstatus_size)
            ps = struct.unpack(self.pathstatus_format, data)
            self.path_status.append({
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

        # call train or infer, return action
        selected_path_id = train_infer(self.path_status, self.module_mode)
        print(f"[Unix socket] Selected path {selected_path_id}")
        conn.sendall(struct.pack('Q', selected_path_id))
