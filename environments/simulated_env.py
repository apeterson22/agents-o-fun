import gym
import numpy as np
from gym import spaces
import pandas as pd
import os
from configs import paths

class SimulatedTradingEnv(gym.Env):
    def __init__(self):
        super(SimulatedTradingEnv, self).__init__()
        self.data = self._load_data()
        if self.data.shape[0] == 0:
            self.num_features = 3
        else:
            self.num_features = self.data.shape[1]

        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.num_features,), dtype=np.float32)
        self.action_space = spaces.Discrete(3)  # 0 = hold, 1 = buy, 2 = sell
        self.current_step = 0

    def _load_data(self):
        if not os.path.exists(paths.TRAINING_DATA_DB):
            return np.zeros((1, 3))
        try:
            import sqlite3
            conn = sqlite3.connect(paths.TRAINING_DATA_DB)
            df = pd.read_sql_query("SELECT feature1, feature2, feature3 FROM training_samples", conn)
            conn.close()
            return df.values if not df.empty else np.zeros((1, 3))
        except Exception as e:
            return np.zeros((1, 3))

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        obs = self.data[self.current_step]
        return obs, {}

    def step(self, action):
        reward = np.random.randn()
        self.current_step += 1
        done = self.current_step >= len(self.data) - 1
        obs = self.data[self.current_step] if not done else np.zeros(self.num_features)
        return obs, reward, done, False, {}

