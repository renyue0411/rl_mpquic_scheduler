import os
import numpy as np

from a2c import a2c_agent, buffer
from a2c.rewards import per_packet_reward, per_file_reward
import envs.config as envs_config
from envs.config import METRICS_DIR

episode = 1

def get_state(path_states):
    state_list = []
    for state in path_states:
        state_list.extend([
            state['CWND'],
            state['QueueSize'],
            state['Send'],
            state['Retrans'],
            state['Lost'],
            state['Received'],
        ])
    return state_list

def get_fct_ofo(episode):
    """
    Get FCT and OFO from log file
    """
    assert episode >= 1, "Episode number must be >= 1"
    fct, ofo = 0, 0
    fct_log = os.path.join(METRICS_DIR, "fct.log")
    ofo_log = os.path.join(METRICS_DIR, "ofo.log")
    with open(fct_log, 'r') as f:
        lines = f.readlines()
        if episode <= len(lines):
            fct_line = lines[episode - 1].strip()
            fct = float(fct_line)
    with open(ofo_log, 'r') as f:
        lines = f.readlines()
        if episode <= len(lines):
            ofo_line = lines[episode - 1].strip()
            ofo = float(ofo_line)
    return fct, ofo

def train_infer(path_status_list, mode, agent=a2c_agent, buffer=buffer):
    # 1. STATE BUILD
    state = get_state(path_status_list)

    # 2. ACTION SELECT
    action_probs = agent.choose_action(state)

    if mode == 'train':
        # select action by probs
        action = np.random.choice(len(action_probs), p=action_probs)

        # calculate reward per packet
        small_reward = per_packet_reward(path_status_list)

        # One-hot action incode
        action_one_hot = np.eye(len(action_probs))[action]

        # record experience
        next_state = state  # use current states while no next states
        buffer.store(state, action_one_hot, small_reward, next_state)

        # add reward per file while file tansfer complete once
        if envs_config.FILE_COMPLETE_FLAG:
            global episode
            fct, ofo = get_fct_ofo(episode)
            big_reward = per_file_reward(fct, ofo)
            buffer.finalize_episode(big_reward)

            # update model
            states, actions, rewards, next_states, dones = buffer.get_batch()
            agent.update(states, actions, rewards, next_states, dones)
            buffer.clear()
            print(f"[Train] Episode {episode} completed with reward: {big_reward:.2f}")
            episode += 1

    elif mode == 'infer':
        # select action by argmax
        action = int(np.argmax(action_probs))

    else:
        raise ValueError(f"[Train_infer] Invalid mode: {mode}")

    # 3. RETURN PATH ID
    selected_path_id = path_status_list[action]['PathID']
    return selected_path_id

