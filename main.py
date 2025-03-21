import asyncio
import logging
import threading
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
import os
import configparser
from concurrent.futures import ThreadPoolExecutor
import json
from core.api_interface import FidelityAPI
from core.crypto_interface import CryptoAPI
from core.betting_interface import BettingAPI
from core.trading_engine import TradingEngine
from core.risk_manager import RiskManager
from core.regulatory_compliance import RegulatoryCompliance
from ai_self_improvement.feature_writer import AdvancedFeatureWriter
from dashboards.monitoring import MonitoringDashboard
from ai_self_improvement.reinforcement_learning import RLTrainer
from ai_self_improvement.genetic_algo import GeneticOptimizer
from ai_self_improvement.training_data_generator import TrainingDataGenerator
import requests
from dotenv import load_dotenv
import sys

sys.setrecursionlimit(10000)

logging.basicConfig(
    filename='logs/main_agent.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    filemode='a',
    force=True
)
logging.info("Logging successfully initialized.")
print("Script Started, logging initialing")
logging.info("Script started correctly.")

try:
    from core.api_interface import FidelityAPI
    from core.crypto_interface import CryptoAPI
    from core.betting_interface import BettingAPI
    from core.risk_manager import RiskManager
    from core.regulatory_compliance import RegulatoryCompliance
    from ai_self_improvement.feature_writer import AdvancedFeatureWriter
    from dashboards.monitoring import MonitoringDashboard
    logging.info("All modules imported successfully.")
    print("All modules imported successfully, script running.")
except Exception as e:
    logging.exception("Module import error:")
    print(f"Module import error: {e}")

load_dotenv()

def setup_logging(log_file: str = 'logs/main_agent.log') -> logging.Logger:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        filemode='a'
    )
    return logging.getLogger(__name__)

class TradingAgent:
    def __init__(self, config_file: str = 'config.ini'):
        self.logger = setup_logging()
        self.config = self.load_config(config_file)
        self.daily_profit = 0.0
        self.last_reset = datetime.now().date()
        self.executor = ThreadPoolExecutor(max_workers=3)

        try:
            self.fidelity_api = FidelityAPI(api_key=os.getenv("FIDELITY_API_KEY", self.config.get('API', 'fidelity_key')))
            self.crypto_api = CryptoAPI(
                coinbase_api_key=os.getenv("COINBASE_KEY", self.config.get('API', 'coinbase_key')),
                cryptocom_api_key=os.getenv("CRYPTOCOM_KEY", self.config.get('API', 'cryptocom_key'))
            )
            self.betting_api = BettingAPI(cryptocom_api_key=os.getenv("CRYPTOCOM_BETTING_KEY", self.config.get('API', 'cryptocom_betting_key')))
        except Exception as e:
            self.logger.error(f"API initialization failed: {e}")
            self.fidelity_api = None
            self.crypto_api = None
            self.betting_api = None

        self.daily_goal = self.config.getfloat('Goals', 'daily_profit')
        self.risk_manager = RiskManager(
            max_daily_loss=self.config.getfloat('Risk', 'max_daily_loss'),
            stop_loss_pct=self.config.getfloat('Risk', 'stop_loss_pct'),
            max_position_size=self.config.getfloat('Risk', 'max_position_size'),
            daily_goal=self.config.getfloat('Goals', 'daily_profit')
        )
        self.compliance = RegulatoryCompliance()
        self.trading_engine = TradingEngine(
            fidelity_api=self.fidelity_api,
            crypto_api=self.crypto_api,
            betting_api=self.betting_api,
            risk_manager=self.risk_manager,
            compliance=self.compliance
        )

        self.feature_writer = AdvancedFeatureWriter()
        self.rl_trainer = RLTrainer()
        self.genetic_optimizer = GeneticOptimizer()
        self.training_data_generator = TrainingDataGenerator()

        self.ai_provider = self.config.get('AI', 'provider')
        self.ai_endpoint = self.config.get('AI', 'endpoint')
        self.ai_api_key = os.getenv("AI_API_KEY", self.config.get('AI', 'api_key', fallback=None))
        self._init_ai_client()

        self.dashboard = MonitoringDashboard(agent=self)
        self.dashboard.integrate_components(self.rl_trainer, self.genetic_optimizer, self.feature_writer)
        threading.Thread(target=self.dashboard.start, daemon=True).start()

    def load_config(self, config_file: str) -> configparser.ConfigParser:
        print("Loading config...")
        config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
        try:
            config.read(config_file)
            if not config.sections():
                raise ValueError("Configuration file is empty or invalid.")
            self.logger.info(f"Configuration loaded from {config_file}")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            raise
        return config

    def _init_ai_client(self) -> None:
        print("Starting Ai Client init...")
        try:
            if self.ai_provider.lower() == 'ollama':
                from ollama import Client
                self.ai_client = Client(host=self.ai_endpoint)
                model_name = self.config.get('AI', 'model')
                response = self.ai_client.generate(model=model_name, prompt="test")
                if 'response' not in response:
                    raise ConnectionError(f"Ollama server at {self.ai_endpoint} is not responding correctly.")
                self.logger.info(f"✅ Ollama initialized at {self.ai_endpoint} with model {model_name}.")

            elif self.ai_provider.lower() == 'openai':
                self.ai_client = lambda prompt: requests.post(
                    "https://api.openai.com/v1/completions",
                    headers={"Authorization": f"Bearer {self.ai_api_key}"},
                    json={"model": "text-davinci-003", "prompt": prompt, "max_tokens": 500}
                ).json()
                self.logger.info("Initialized OpenAI client")

            elif self.ai_provider.lower() == 'grok':
                self.ai_client = lambda prompt: requests.post(
                    "https://api.x.ai/v1/grok",
                    headers={"Authorization": f"Bearer {self.ai_api_key}"},
                    json={"prompt": prompt}
                ).json()
                self.logger.info("Initialized Grok client")

            else:
                raise ValueError(f"❌ Unsupported AI provider: {self.ai_provider}. Options: ollama, openai, grok.")

        except Exception as e:
            self.logger.error(f"❌ AI client initialization failed: {e}")
            self.ai_client = None

    def train_only_mode(self): # -> None:
        self.logger.info("Training Mode Activated: Running AI Training...")
        return asyncio.create_task(self._train_only_async())

    async def _train_only_async(self):
        self.logger.info("Async Training Mode Activated: Running AI Training...")
        self.training_data_generator.generate_and_store_all(
            synthetic_count=300,
            trade_log_limit=500,
            mode="default"
        )

        if self.rl_trainer:
            self.logger.info("Running RL Training...")
            self.rl_trainer.train_model(timesteps=10000, data_mode="default")

        if self.genetic_optimizer:
            self.logger.info("Running Genetic Algorithm Optimization...")
            best_params = self.genetic_optimizer.run_optimization()
            if best_params:
                self.logger.info(f"Optimized parameters found: {best_params}")

        if self.feature_writer:
            self.logger.info("Running Feature Engineering...")
            module = self.feature_writer.load_feature("sample_feature")
            if module:
                sample_data = self.training_data_generator.get_samples_by_tag("default")
#                sample_data = self.training_data_generator.get_samples_by_tag("synthetic")
                self.feature_writer.evaluate_feature(module, sample_data)

        self.logger.info("Training Mode Complete.")

async def main() -> None:
    agent = TradingAgent()
    await agent.train_only_mode()  # Or replace with trading_loop if needed

if __name__ == "__main__":
    print("Main has begun...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("AI Trading agent stopped by user.")
    except Exception as e:
        print(f"Error Encountered: {e}")
        logging.exception(f"Unhandled exception: {e}")
        logging.error(f"Main execution failed: {e}")

