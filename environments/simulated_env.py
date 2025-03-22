from gymnasium import Env, spaces 
import numpy as np

class SimulatedTradingEnv(Env):
    def __init__(self, initial_data=None, window_size=10):
        super(SimulatedTradingEnv, self).__init__()

        self.window_size = window_size
        self.current_step = 0

        self.data = initial_data if initial_data is not None else self._generate_default_data()
        self.num_features = self.data.shape[1] if len(self.data.shape) > 1 else 1

        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.window_size, self.num_features), dtype=np.float32)
        self.action_space = spaces.Discrete(3)  # Buy, Sell, Hold

        self.cash = 10000
        self.holdings = 0
        self.portfolio_value = self.cash

    def _generate_default_data(self, num_steps=1000):
        # Generate dummy price data with 1 feature (e.g., closing price)
        return np.cumsum(np.random.randn(num_steps, 1)) + 100

    def update_data(self, new_data):
        self.data = new_data
        self.num_features = self.data.shape[1] if len(self.data.shape) > 1 else 1
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.window_size, self.num_features), dtype=np.float32)
        self.reset()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        self.cash = 10000
        self.holdings = 0
        self.portfolio_value = self.cash
        return self._next_observation(), {}

    def _next_observation(self):
        start = self.current_step
        end = start + self.window_size
        obs = self.data[start:end]
        if obs.shape[0] < self.window_size:
            obs = np.pad(obs, ((0, self.window_size - obs.shape[0]), (0, 0)), mode='constant')
        return obs.astype(np.float32)

    def step(self, action):
        price = self.data[self.current_step + self.window_size - 1][0]

        if action == 0:  # Buy
            num_shares = self.cash // price
            self.cash -= num_shares * price
            self.holdings += num_shares
        elif action == 1:  # Sell
            self.cash += self.holdings * price
            self.holdings = 0
        # Hold is a no-op

        self.current_step += 1
        done = self.current_step + self.window_size >= len(self.data)

        self.portfolio_value = self.cash + self.holdings * price
        reward = self.portfolio_value / 10000 - 1

        obs = self._next_observation()
        info = {
            "step": self.current_step,
            "cash": self.cash,
            "holdings": self.holdings,
            "portfolio_value": self.portfolio_value,
            "price": price
        }
        return obs, reward, done, False, info

    def render(self, mode='human'):
        print(f"Step: {self.current_step}, Cash: {self.cash}, Holdings: {self.holdings}, Portfolio Value: {self.portfolio_value}")

