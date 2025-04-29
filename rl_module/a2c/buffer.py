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
        if self.rewards:
            self.rewards[-1] += final_reward
            self.dones[-1] = 1.0

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