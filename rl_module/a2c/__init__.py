from rl_module.a2c.utils import STATE_DIM, ACTION_DIM, HIDDEN_DIM, A_LR, C_LR, GAMMA, TEMP
from rl_module.a2c.agent import A2CAgent
from rl_module.a2c.buffer import EpisodeBuffer

# create an A2C agent
a2c_agent = A2CAgent(STATE_DIM, ACTION_DIM, HIDDEN_DIM, A_LR, C_LR, GAMMA, TEMP)

# create a buffer for saving parameters every episode
buffer = EpisodeBuffer()