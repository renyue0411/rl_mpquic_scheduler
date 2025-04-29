from utils import STATE_DIM, ACTION_DIM, HIDDEN_DIM, A_LR, C_LR, GAMMA
from agent import A2CAgent
from buffer import EpisodeBuffer

# create an A2C agent
a2c_agent = A2CAgent(STATE_DIM, ACTION_DIM, HIDDEN_DIM, A_LR, C_LR, GAMMA)

# create a buffer for saving parameters every episode
buffer = EpisodeBuffer()