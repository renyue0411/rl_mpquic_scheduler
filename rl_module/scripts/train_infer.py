# scripts/run_agent.py
import os
import socket
import struct
import json
import argparse
import numpy as np
import torch
from a3c.agent import A2CAgent
from a3c.utils import STATE_DIM, ACTION_DIM, GAMMA, A_LR, C_LR
from envs.mininet_env import MPQUICEnv

SOCKET_PATH = "/tmp/mpquic_socket"
MODEL_SAVE_PATH = "/home/server/Desktop/rl_scheduler_mpquic/models/actor_critic_final.pth"
REWARD_RECORD_PATH = "/home/server/Desktop/rl_scheduler_mpquic/log/rewards_record.json"

TOPO_SCRIPT_PATH = "/home/server/Desktop/rl_scheduler_mpquic/scripts/your_mininet_topo.py"
QUIC_CLIENT_PATH = "/home/server/Desktop/rl_scheduler_mpquic/scripts/your_quic_client.sh"
LOG_DIR = "/home/server/Desktop/rl_scheduler_mpquic/log"

pathstatus_format = '10Q'
pathstatus_size = 80
num_episodes = 1000

def run(mode):
    env = MPQUICEnv(TOPO_SCRIPT_PATH, QUIC_CLIENT_PATH, LOG_DIR)
    agent = A2CAgent(state_dim=STATE_DIM, action_dim=ACTION_DIM, actor_lr=A_LR, critic_lr=C_LR, gamma=GAMMA)

    if os.path.exists(MODEL_SAVE_PATH):
        agent.load_model(MODEL_SAVE_PATH)
    elif mode == 'infer':
        raise FileNotFoundError("No trained model found for inference!")

    all_rewards = []

    for episode in range(1, num_episodes + 1):
        env.reset()

        episode_states = []
        episode_actions = []
        episode_rewards = []
        episode_next_states = []
        episode_dones = []

        done = False

        while not done:
            state = receive_path_status()

            action_probs = agent.choose_action(state)
            action = np.random.choice(len(action_probs), p=action_probs)

            send_action(action)

            next_state = receive_path_status()

            # 小reward（这里只是简单示例）
            small_reward = -np.sum(state[2::4])

            action_one_hot = np.zeros_like(action_probs)
            action_one_hot[action] = 1

            if mode == 'train':
                episode_states.append(state)
                episode_actions.append(action_one_hot)
                episode_rewards.append(small_reward)
                episode_next_states.append(next_state)
                episode_dones.append(0.0)

            state = next_state

            if check_file_complete(next_state):
                env.wait_file_complete()

                if mode == 'train':
                    fct, loss, ofo = env.read_logs()
                    big_reward = env.compute_file_reward(fct, loss, ofo)
                    episode_rewards[-1] += big_reward
                    episode_dones[-1] = 1.0

                done = True

        if mode == 'train':
            agent.update(episode_states, episode_actions, episode_rewards, episode_next_states, episode_dones)
            total_reward = sum(episode_rewards)
            all_rewards.append(total_reward)

            if episode % 10 == 0:
                print(f"[Train] Episode {episode} Total reward: {total_reward:.4f}")

            if episode % 100 == 0:
                torch.save(agent.model.state_dict(), MODEL_SAVE_PATH)
                with open(REWARD_RECORD_PATH, 'w') as f:
                    json.dump(all_rewards, f)

        else:
            print(f"[Infer] Episode {episode} completed.")

    env.close()
    print(f"[{mode.capitalize()}] Finished!")

def receive_path_status():
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)

    num_paths_data = client.recv(4)
    num_paths = struct.unpack('<I', num_paths_data)[0]

    path_status = []
    for _ in range(num_paths):
        data = client.recv(pathstatus_size)
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

    client.close()
    return pathstatus_to_state(path_status)

def send_action(action):
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(SOCKET_PATH)
    client.sendall(struct.pack('i', action))
    client.close()

def pathstatus_to_state(path_status_list):
    state = []
    for path in path_status_list:
        srtt = path['SRTT'] / 1000000.0
        cwnd = path['CWND'] / 10000.0
        queue = path['QueueSize'] / 10000.0
        loss_rate = (path['Lost'] / max(1, path['Send'])) if path['Send'] > 0 else 0.0
        state.extend([cwnd, srtt, queue, loss_rate])
    return np.array(state)

def check_file_complete(state):
    # 简化假设，根据你的实际PathStatus内容判断
    return False  # 暂时留空，需要完善

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, choices=['train', 'infer'], required=True)
    args = parser.parse_args()

    run(args.mode)
