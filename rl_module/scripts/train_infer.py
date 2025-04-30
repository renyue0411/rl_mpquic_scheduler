import os
import json
import numpy as np

from rl_module.a2c import a2c_agent, buffer
from rl_module.a2c.rewards import per_packet_reward, per_file_reward
from rl_module.a2c.utils import REWARD_RECORD_PATH
import rl_module.envs.config as config
from rl_module.envs.config import METRICS_DIR


class A2CTrainer:
    def __init__(self, agent=a2c_agent, buffer=buffer, reward_dir=REWARD_RECORD_PATH, metric_dir=METRICS_DIR):
        self.agent = agent
        self.buffer = buffer
        self.episode = 1
        self.reward_packet_path = os.path.join(reward_dir, "reward_per_packet.json")
        self.reward_file_path = os.path.join(reward_dir, "reward_per_file.json")
        self.metric_dir = metric_dir
        self.last_state = None
        self.last_action = None
        self.last_reward = None
        self.last_path_status_list = None

    def _get_state(self, path_status_list):
        state_list = []
        for state in path_status_list:
            state_list.extend([
                state['CWND'],
                state['QueueSize'],
                state['Send'],
                state['Retrans'],
                state['Lost'],
                state['Received'],
            ])
        return state_list

    def _get_fct_ofo(self, episode):
        fct, ofo = 0, 0
        fct_log = os.path.join(self.metric_dir, "fct.log")
        ofo_log = os.path.join(self.metric_dir, "ofo.log")
        with open(fct_log, 'r') as f:
            lines = f.readlines()
            if episode <= len(lines):
                fct = float(lines[episode - 1].strip())
        with open(ofo_log, 'r') as f:
            lines = f.readlines()
            if episode <= len(lines):
                ofo = float(lines[episode - 1].strip())
        return fct, ofo

    def log_reward(self, value, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                rewards = json.load(f)
        else:
            rewards = []
        rewards.append(value)
        with open(path, 'w') as f:
            json.dump(rewards, f)

    def train_step(self, path_status_list):
        # 当前包状态
        state = self._get_state(path_status_list)

        # 当前包其实属于新文件，意味着上一包是终止包
        if config.get_file_complete_flag() == True:
            if self.last_state is not None:
                small_reward = per_packet_reward(self.last_path_status_list)
                self.last_reward = small_reward
                print(f"[Train] per packet reward: {self.last_reward}")
                self.log_reward(self.last_reward, self.reward_packet_path)
                self.buffer.store(self.last_state, self.last_action, self.last_reward, self.last_state, done=1.0)

            # 然后进行上一 episode 的训练更新
            fct, ofo = self._get_fct_ofo(self.episode)
            big_reward = per_file_reward(fct, ofo)
            self.log_reward(big_reward, self.reward_file_path)

            print(f"[Train] Episode {self.episode} FCT: {fct}, OFO: {ofo}")
            print(f"[Train] Episode {self.episode} completed with reward: {big_reward:.2f}")

            self.buffer.distribute_file_reward(big_reward)
            states, actions, rewards, next_states, dones = self.buffer.get_batch()
            self.agent.update(states, actions, rewards, next_states, dones)
            self.buffer.clear()
            config.set_file_complete_flag(False)
            print(f"[Mininet] file transfer again, status: {config.FILE_COMPLETE_FLAG}")
            self.episode += 1

            # 重置 last 缓存（因为当前包是新 episode 的第一包）
            self.last_state = None
            self.last_action = None
            self.last_path_status_list = None

        # 如果 last 还存在，就补存上一次的 transition
        if self.last_state is not None:
            small_reward = per_packet_reward(self.last_path_status_list)
            self.last_reward = small_reward
            print(f"[Train] per packet reward: {self.last_reward}")
            self.log_reward(self.last_reward, self.reward_packet_path)
            self.buffer.store(self.last_state, self.last_action, self.last_reward, state)

        # 当前包决策
        action_probs = self.agent.choose_action(state)
        action = np.random.choice(len(action_probs), p=action_probs)

        # 更新缓存
        self.last_state = state
        self.last_action = action
        self.last_path_status_list = path_status_list

        return path_status_list[action]['PathID']


    def infer_step(self, path_status_list):
        state = self._get_state(path_status_list)
        action_probs = self.agent.choose_action(state)
        action = int(np.argmax(action_probs))
        return path_status_list[action]['PathID']
