# scripts/run_unix_socket.py
import os
import socket
import struct
import argparse
from scripts.run_agent import infer_action  # 只引入推理方法

SOCKET_PATH = "/tmp/mpquic_socket"
pathstatus_format = '10Q'
pathstatus_size = struct.calcsize(pathstatus_format)

def handle_connection(conn):
    num_paths_data = conn.recv(4)
    num_paths = struct.unpack('<I', num_paths_data)[0]

    path_status = []
    for _ in range(num_paths):
        data = conn.recv(pathstatus_size)
        ps = struct.unpack(pathstatus_format, data)
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

    # 直接调用推理方法，返回动作
    selected_path_id = infer_action(path_status)
    conn.sendall(struct.pack('Q', selected_path_id))

def main():
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(SOCKET_PATH)
        server.listen()
        print(f"[Socket server started] Listening at {SOCKET_PATH}")

        while True:
            conn, _ = server.accept()
            with conn:
                handle_connection(conn)

if __name__ == '__main__':
    main()
