import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

from rl_module.a2c.model import ActorCritic

class A2CAgent:
    def __init__(self, state_dim, action_dim, hidden_dim, actor_lr, critic_lr, gamma):
        self.model = ActorCritic(state_dim, action_dim, hidden_dim)
        self.actor_optimizer = optim.Adam(self.model.actor.parameters(), lr=actor_lr)
        self.critic_optimizer = optim.Adam(self.model.critic.parameters(), lr=critic_lr)
        self.gamma = gamma

    def choose_action(self, state):
        """
        input current states, output probs
        """
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            probs, _ = self.model(state_tensor)
        return probs.squeeze(0).numpy()

    def compute_loss(self, states, actions, rewards, next_states, dones):
        """
        Calculate Actor Loss and Critic Loss
        """
        states = torch.FloatTensor(states)
        next_states = torch.FloatTensor(next_states)
        actions = torch.FloatTensor(actions)
        rewards = torch.FloatTensor(rewards)
        dones = torch.FloatTensor(dones)

        policy_dists, state_values = self.model(states)
        _, next_state_values = self.model(next_states)

        td_target = rewards + self.gamma * next_state_values.squeeze(1) * (1 - dones)
        td_error = td_target.detach() - state_values.squeeze(1)

        critic_loss = td_error.pow(2).mean()

        action_log_probs = torch.log((policy_dists + 1e-8) * actions).sum(dim=1)
        actor_loss = -(action_log_probs * td_error.detach()).mean()

        print(f"[Update] Actor loss: {actor_loss.item():.4f}, Critic loss: {critic_loss.item():.4f}")
        return actor_loss, critic_loss

    def update(self, states, actions, rewards, next_states, dones):
        """
        Update parameters of Actor and Critic using new states
        """
        actor_loss, critic_loss = self.compute_loss(states, actions, rewards, next_states, dones)

        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()

        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

    def save_model(self, save_path):
        torch.save(self.model.state_dict(), save_path)

    def load_model(self, load_path):
        self.model.load_state_dict(torch.load(load_path, map_location=torch.device('cpu')))
        self.model.eval()
