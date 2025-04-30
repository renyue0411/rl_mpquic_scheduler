import os
import socket
import struct

from rl_module.scripts.train_infer import A2CTrainer
from rl_module.a2c import a2c_agent, buffer
from rl_module.a2c.utils import SOCKET_PATH

class UnixSocketServer:
    def __init__(self, module_mode, socket_path=SOCKET_PATH, agent=a2c_agent, buffer=buffer):
        self.socket_path = socket_path
        self.module_mode = module_mode
        self.pathstatus_format = '9Q'
        self.pathstatus_size = struct.calcsize(self.pathstatus_format)
        self.trainer = A2CTrainer(agent=agent, buffer=buffer)
    
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
            })

        # print(f"[Unix socket] Received {num_paths} path states.")
        # for ps in path_status:
        #     print(f" → PathID {ps['PathID']}, CWND {ps['CWND']}, RTT {ps['SRTT']}, Queue {ps['QueueSize']}, Loss {(ps['Retrans'] + ps['Lost']) / max(1, ps['Retrans'] + ps['Lost'] + ps['Send']):.2f}, Received {ps['Received']}")
        # call train or infer, return action
        if self.module_mode == "train":
            selected_path_id = self.trainer.train_step(path_status)
        elif self.module_mode == "infer":
            selected_path_id = self.trainer.infer_step(path_status)
        # print(f"[Unix socket] Selected path {selected_path_id}")
        conn.sendall(struct.pack('Q', selected_path_id))
