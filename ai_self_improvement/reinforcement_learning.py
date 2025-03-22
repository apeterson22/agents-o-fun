import os
import time
import logging
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.env_util import make_vec_env
from environments.simulated_env import SimulatedTradingEnv
from utils.stats_tracker import SharedStatsTracker


class RLTrainer:
    def __init__(self, model_path='models/ppo_trading_model.zip'):
        self.model_path = model_path
        self.env = DummyVecEnv([lambda: SimulatedTradingEnv()])
        self.model = PPO("MlpPolicy", self.env, verbose=0)
        self.stats_tracker = SharedStatsTracker.get_instance()

        if os.path.exists(self.model_path):
            self.model = PPO.load(self.model_path, env=self.env)
            logging.info("RL model loaded from checkpoint.")
        else:
            logging.info("Training new RL model.")

    def train(self, total_timesteps=10000):
        logging.info(f"Training RL model for {total_timesteps} steps.")
        self.model.set_env(self.env)
        episode_rewards = []

        obs = self.env.reset()
        for step in range(total_timesteps):
            action, _ = self.model.predict(obs, deterministic=True)
            obs, reward, done, _, info = self.env.step(action)

            portfolio_value = info[0].get("portfolio_value", 0)
            current_stats = {
                "step": step,
                "reward": float(reward[0]),
                "portfolio_value": float(portfolio_value),
            }
            self.stats_tracker.update_stats(current_stats)

            if done:
                episode_rewards.append(float(reward[0]))
                self.stats_tracker.push_episode_summary({
                    "episode_reward": float(reward[0]),
                    "step": step,
                    "portfolio_value": float(portfolio_value)
                })
                obs = self.env.reset()

        self.model.save(self.model_path)
        logging.info(f"RL model trained successfully for {total_timesteps} steps.")

    def get_latest_stats(self):
        return self.stats_tracker.get_stats()

    def get_episode_summaries(self):
        return self.stats_tracker.get_episode_summaries()

    def update_env_data(self, new_data):
        if hasattr(self.env.envs[0], 'update_data'):
            self.env.envs[0].update_data(new_data)
            logging.info("Environment data updated dynamically.")
