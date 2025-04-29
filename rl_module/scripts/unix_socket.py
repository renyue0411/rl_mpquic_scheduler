# scripts/run_unix_socket.py
import os
import socket
import struct
import argparse
import numpy as np
from a3c.agent import A2CAgent
from a3c.utils import ACTION_DIM, STATE_DIM, GAMMA, A_LR, C_LR

SOCKET_PATH = "/tmp/mpquic_socket"
MODEL_SAVE_PATH = "/home/server/Desktop/rl_scheduler_mpquic/models/actor_critic_final.pth"

pathstatus_format = '10Q'
pathstatus_size = struct.calcsize(pathstatus_format)

# 初始化Agent
agent = A2CAgent(state_dim=STATE_DIM, action_dim=ACTION_DIM, actor_lr=A_LR, critic_lr=C_LR, gamma=GAMMA)

# 如果存在已保存模型，加载
if os.path.exists(MODEL_SAVE_PATH):
    agent.load_model(MODEL_SAVE_PATH)

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

    state = pathstatus_to_state(path_status)
    action = agent.choose_action(state).argmax()

    selected_path_id = path_status[action]['PathID']
    conn.sendall(struct.pack('Q', selected_path_id))

def pathstatus_to_state(path_status_list):
    state = []
    for path in path_status_list:
        srtt = path['SRTT'] / 1000000.0
        cwnd = path['CWND'] / 10000.0
        queue = path['QueueSize'] / 10000.0
        loss_rate = (path['Lost'] / max(1, path['Send'])) if path['Send'] > 0 else 0.0
        state.extend([cwnd, srtt, queue, loss_rate])
    return np.array(state)

def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

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
