import os
import socket
import struct
import json
import numpy as np
import torch

from a2c import a2c_agent

class EpisodeBuffer:
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []

    def store(self, state, action_one_hot, reward, next_state, done=0.0):
        self.states.append(state)
        self.actions.append(action_one_hot)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)

    def finalize_episode(self, final_reward):
        """Add final reward to the last step, and mark done = 1.0"""
        if self.rewards:
            self.rewards[-1] += final_reward
            self.dones[-1] = 1.0

    def is_ready(self):
        return len(self.states) > 0

    def clear(self):
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.next_states.clear()
        self.dones.clear()

    def get_batch(self):
        return (
            self.states,
            self.actions,
            self.rewards,
            self.next_states,
            self.dones
        )

def train_infer(state, mode):
    """
    train or infer mode return action (selected path)
    """
    action_probs = a2c_agent.choose_action(state)

    if mode == 'train':
        # 按概率采样动作
        action = np.random.choice(len(action_probs), p=action_probs)

        # 小奖励设计
        small_reward = -np.sum(state[2::4])

        # One-hot编码动作
        action_one_hot = np.zeros_like(action_probs)
        action_one_hot[action] = 1

        return action, small_reward, action_one_hot

    elif mode == 'infer':
        # 直接取最大概率的动作（贪婪）
        action = np.argmax(action_probs)
        return action

    else:
        raise ValueError(f"[train_infer] Invalid mode: {mode}, must be 'train' or 'infer'")

