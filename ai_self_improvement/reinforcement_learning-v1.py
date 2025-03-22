import logging
import os
from typing import Optional
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback
import gym
import torch
from ai_self_improvement.training_data_generator import TrainingDataGenerator
import numpy as np
np.bool8 = np.bool_

def setup_logging(log_file: str = 'logs/rl_training.log') -> None:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s]: %(message)s',
        filemode='a'
    )

class RLTrainer:
    def __init__(self, env_id: str = 'CartPole-v1', n_envs: int = 4) -> None:
        if not isinstance(n_envs, int) or n_envs <= 0:
            raise ValueError("n_envs must be a positive integer")

        self.env_id = env_id
        self.n_envs = n_envs
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.training_data = TrainingDataGenerator()

        try:
            self.env = make_vec_env(env_id, n_envs=n_envs)
            self.eval_env = gym.make(env_id)
        except gym.error.Error as e:
            logging.error(f"Failed to create environment: {e}")
            raise

    def train_model(self, timesteps: int = 50000, save_path: str = "configs/ppo_trading_model", data_mode: str = "default") -> bool:
        if not isinstance(timesteps, int) or timesteps <= 0:
            logging.error("Timesteps must be a positive integer")
            raise ValueError("Timesteps must be a positive integer")

        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Generate training samples before model training
            self.training_data.generate_and_store_all(
                synthetic_count=200,
                trade_log_limit=300,
                mode=data_mode
            )

            model = PPO(
                policy='MlpPolicy',
                env=self.env,
                verbose=1,
                device=self.device,
                learning_rate=3e-4,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                gae_lambda=0.95,
                clip_range=0.2,
                ent_coef=0.01,
            )

            eval_callback = EvalCallback(
                self.eval_env,
                best_model_save_path=save_path + "_best",
                log_path="logs/",
                eval_freq=max(10000 // self.n_envs, 1),
                deterministic=True,
                render=False
            )

            model.learn(
                total_timesteps=timesteps,
                callback=eval_callback,
                progress_bar=False,
                tb_log_name="ppo_training"
            )

            model.save(save_path)
            logging.info(f"RL model trained successfully for {timesteps} steps.")
            return True

        except Exception as e:
            logging.error(f"Error during RL training: {e}")
            return False

    def load_model(self, path: str = "configs/ppo_trading_model.zip") -> Optional[PPO]:
        if not os.path.exists(path):
            logging.error(f"Model file not found at: {path}")
            return None

        try:
            model = PPO.load(path, env=self.env, device=self.device)
            logging.info("RL model loaded successfully.")
            return model
        except Exception as e:
            logging.error(f"Error loading RL model: {e}")
            return None

    def __del__(self) -> None:
        if hasattr(self, 'env'):
            self.env.close()
        if hasattr(self, 'eval_env'):
            self.eval_env.close()

if __name__ == "__main__":
    setup_logging()
    try:
        trainer = RLTrainer(n_envs=4)
        success = trainer.train_model(timesteps=100000)
        if success:
            model = trainer.load_model()
            if model:
                logging.info("Training and loading completed successfully")
    except Exception as e:
        logging.error(f"Main execution failed: {e}")

