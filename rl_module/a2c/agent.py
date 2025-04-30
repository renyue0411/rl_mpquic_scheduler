import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from rl_module.a2c.model import ActorCritic

class A2CAgent:
    def __init__(self, state_dim, action_dim, hidden_dim, actor_lr, critic_lr, gamma, temperature=5.0):
        self.model = ActorCritic(state_dim, action_dim, hidden_dim, temperature)
        self.actor_optimizer = optim.Adam(self.model.actor_head.parameters(), lr=actor_lr)
        self.critic_optimizer = optim.Adam(self.model.critic_head.parameters(), lr=critic_lr)
        self.gamma = gamma

    def choose_action(self, state):
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            probs, _ = self.model(state_tensor)
        probs = probs.squeeze(0).numpy()

        # 探索异常修正
        if np.any(np.isnan(probs)) or np.sum(probs) <= 0:
            print("[Warning] Invalid probs detected:", probs)
            probs = np.ones_like(probs) / len(probs)

        # ε-greedy 探索
        if np.random.rand() < 0.1:
            action = np.random.choice(len(probs))
        else:
            action = np.random.choice(len(probs), p=probs)
        return probs

    def compute_loss(self, states, actions, rewards, next_states, dones):
        states = torch.FloatTensor(states)
        next_states = torch.FloatTensor(next_states)
        actions = torch.LongTensor(actions).unsqueeze(1)
        rewards = torch.FloatTensor(rewards)
        dones = torch.FloatTensor(dones)

        policy_dists, state_values, logits = self.model(states, return_logits=True)
        _, next_state_values = self.model(next_states)

        td_target = rewards + self.gamma * next_state_values.squeeze(1) * (1 - dones)
        td_error = td_target.detach() - state_values.squeeze(1)

        # Critic Loss
        critic_loss = td_error.pow(2).mean()

        # Actor Loss + entropy
        log_probs = torch.log(policy_dists + 1e-8)
        selected_log_probs = log_probs.gather(1, actions).squeeze(1)
        entropy = -(policy_dists * log_probs).sum(dim=1).mean()
        actor_loss = -(selected_log_probs * td_error.detach()).mean() - 0.005 * entropy

        # Debug
        print("[Update] Actor loss: {:.6f}, Critic loss: {:.4f}".format(actor_loss.item(), critic_loss.item()))
        print("[Debug] td_target:", td_target[:5])
        print("[Debug] V(s):", state_values.squeeze(1)[:5])
        print("[Debug] td_error:", td_error[:5])
        print("[Debug] log_prob * td_error:", (selected_log_probs * td_error.detach())[:5])
        print("[Debug] policy_dists:", policy_dists[:5])
        print("[Debug] logits:", logits[:5])

        return actor_loss, critic_loss

    def update(self, states, actions, rewards, next_states, dones):
        actions = np.array(actions)

        actor_loss, critic_loss = self.compute_loss(states, actions, rewards, next_states, dones)

        self.actor_optimizer.zero_grad()
        self.critic_optimizer.zero_grad()
        total_loss = actor_loss + critic_loss
        total_loss.backward()
        self.actor_optimizer.step()
        self.critic_optimizer.step()

    def save_model(self, save_path):
        torch.save(self.model.state_dict(), save_path)

    def load_model(self, load_path):
        self.model.load_state_dict(torch.load(load_path, map_location=torch.device('cpu')))
        self.model.eval()
