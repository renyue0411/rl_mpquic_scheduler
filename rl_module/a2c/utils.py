# state dimension
STATE_DIM = 12  # 2 paths * 6 states

# action dimension
ACTION_DIM = 2  # path 1 or path 3

# discount factor: gamma
GAMMA = 0.99

# learning rate
A_LR = 1e-4  # Actor
C_LR = 1e-3  # Critic

# nn layers
HIDDEN_DIM = 128

TEMP = 5

SOCKET_PATH = "/tmp/mpquic_socket"
EPISODES = 100

MODEL_SAVE_PATH = "/home/server/Desktop/rl_mpquic_scheduler/rl_module/models"
REWARD_RECORD_PATH = "/home/server/Desktop/rl_mpquic_scheduler/rl_module/log"