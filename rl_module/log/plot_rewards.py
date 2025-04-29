# log/plot_rewards.py
import matplotlib.pyplot as plt
import json
import os

def plot_rewards(reward_record_path, save_plot_path):
    with open(reward_record_path, 'r') as f:
        rewards = json.load(f)

    episodes = list(range(1, len(rewards) + 1))

    plt.figure(figsize=(10, 6))
    plt.plot(episodes, rewards, label='Total Reward per Episode', linewidth=2)
    plt.xlabel('Episode')
    plt.ylabel('Total Reward')
    plt.title('Training Reward Curve')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(save_plot_path)
    plt.show()

if __name__ == '__main__':
    base_dir = "/home/server/Desktop/rl_scheduler_mpquic"
    reward_record_path = os.path.join(base_dir, "log", "rewards_record.json")
    save_plot_path = os.path.join(base_dir, "log", "reward_curve.png")

    plot_rewards(reward_record_path, save_plot_path)
