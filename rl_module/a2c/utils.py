# a3c/utils.py

# 状态空间维度
STATE_DIM = 10  # 2条路径 × 每条4个特征

# 动作空间维度
ACTION_DIM = 2  # 选择哪条路径（例如path1/path2）

# 折扣因子（未来奖励权重）
GAMMA = 0.99

# 学习率（Actor和Critic分开）
A_LR = 1e-4  # Actor学习率
C_LR = 1e-3  # Critic学习率

# nn layers
HIDDEN_DIM = 128

# 其他（可以根据需要再补充）
# 比如最大episode数量，batch_size等等

SOCKET_PATH = "/tmp/mpquic_socket"
EPISODES = 100

MODEL_SAVE_PATH = "/home/server/Desktop/rl_mpquic_scheduler/models/"
REWARD_RECORD_PATH = "/home/server/Desktop/rl_mpquic_scheduler/rl_module/log/rewards.json"