import logging
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

logging.basicConfig(
    filename="logs/main_agent.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s"
)

class RLTrainer:
    def __init__(self, env):
        self.env = DummyVecEnv([lambda: env])
        self.model = PPO("MlpPolicy", self.env, verbose=1)

    def train(self, total_timesteps=10000):
        logging.info("Training new RL model.")
        logging.info(f"Training RL model for {total_timesteps} steps.")
        self.model.learn(total_timesteps=total_timesteps)

