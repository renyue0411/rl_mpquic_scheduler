import torch
import torch.nn as nn

class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dim, temperature=5.0):
        super(ActorCritic, self).__init__()
        self.temperature = temperature

        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU()
        )
        self.actor_head = nn.Linear(hidden_dim, action_dim)
        self.critic_head = nn.Linear(hidden_dim, 1)

        self.apply(self.init_weights)

    def forward(self, state, return_logits=False):
        x = self.shared(state)
        logits = self.actor_head(x)

        # temperature & clamp
        scaled_logits = logits / self.temperature
        clipped_logits = torch.clamp(scaled_logits, min=-10.0, max=10.0)
        policy = torch.softmax(clipped_logits, dim=-1)

        value = self.critic_head(x)

        if return_logits:
            return policy, value, clipped_logits
        else:
            return policy, value

    def init_weights(self, m):
        if isinstance(m, nn.Linear):
            nn.init.xavier_uniform_(m.weight)
            nn.init.zeros_(m.bias)
