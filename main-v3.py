import asyncio
import logging
import os
import configparser
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import requests
import sys
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from dashboards.monitoring import MonitoringDashboard
from ai_self_improvement.reinforcement_learning import RLTrainer
from ai_self_improvement.feature_writer import AdvancedFeatureWriter
from ai_self_improvement.genetic_algo import GeneticOptimizer
from ai_self_improvement.training_data_generator import TrainingDataGenerator
from utils.stats_tracker import SharedStatsTracker
from core.api_interface import FidelityAPI
from core.crypto_interface import CryptoAPI
from core.betting_interface import BettingAPI
from core.trading_engine import TradingEngine
from core.risk_manager import RiskManager
from core.regulatory_compliance import RegulatoryCompliance
from dotenv import load_dotenv

sys.setrecursionlimit(10000)

logging.basicConfig(
    filename='logs/main_agent.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    filemode='a',
    force=True
)

load_dotenv()

api_app = FastAPI()
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TradingAgent:
    def __init__(self, config_file: str = 'config.ini'):
        self.logger = logging.getLogger("TradingAgent")
        self.config = self.load_config(config_file)
        self.executor = ThreadPoolExecutor(max_workers=3)

        self.fidelity_api = FidelityAPI(api_key=os.getenv("FIDELITY_API_KEY", self.config.get('API', 'fidelity_key')))
        self.crypto_api = CryptoAPI(
            coinbase_api_key=os.getenv("COINBASE_KEY", self.config.get('API', 'coinbase_key')),
            cryptocom_api_key=os.getenv("CRYPTOCOM_KEY", self.config.get('API', 'cryptocom_key'))
        )
        self.betting_api = BettingAPI(cryptocom_api_key=os.getenv("CRYPTOCOM_BETTING_KEY", self.config.get('API', 'cryptocom_betting_key')))

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
        self.stats_tracker = SharedStatsTracker.get_instance()

        self.ai_provider = self.config.get('AI', 'provider')
        self.ai_endpoint = self.config.get('AI', 'endpoint')
        self.ai_api_key = os.getenv("AI_API_KEY", self.config.get('AI', 'api_key', fallback=None))

        self._init_ai_client()

        self.dashboard = MonitoringDashboard(agent=self)
        self.dashboard.integrate_components(self.rl_trainer, self.genetic_optimizer, self.feature_writer)
        threading.Thread(target=self.dashboard.start, daemon=True).start()

    def load_config(self, config_file: str):
        config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
        config.read(config_file)
        return config

    def _init_ai_client(self):
        try:
            if self.ai_provider.lower() == 'ollama':
                from ollama import Client
                self.ai_client = Client(host=self.ai_endpoint)
                model_list = self.ai_client.list().get("models", [])
                available_models = [m["name"] for m in model_list]

                if available_models:
                    self.config.set('AI', 'available_models', ",".join(available_models))
                    with open('config.ini', 'w') as configfile:
                        self.config.write(configfile)

                selected_model = self.config.get('AI', 'model', fallback=available_models[0] if available_models else 'deepseek-r1:8b')
                response = self.ai_client.generate(model=selected_model, prompt="test")
                if 'response' not in response:
                    raise ConnectionError("Ollama server not responding correctly")

            elif self.ai_provider.lower() == 'openai':
                response = requests.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.ai_api_key}"}
                )
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    available_models = [m["id"] for m in models]
                    if available_models:
                        self.config.set('AI', 'available_models', ",".join(available_models))
                        with open('config.ini', 'w') as configfile:
                            self.config.write(configfile)
                else:
                    raise ConnectionError("Failed to retrieve OpenAI models")

                model_name = self.config.get('AI', 'model', fallback='text-davinci-003')
                self.ai_client = lambda prompt: requests.post(
                    "https://api.openai.com/v1/completions",
                    headers={"Authorization": f"Bearer {self.ai_api_key}"},
                    json={"model": model_name, "prompt": prompt, "max_tokens": 500}
                ).json()
            else:
                raise ValueError(f"Unsupported AI provider: {self.ai_provider}")
        except Exception as e:
            self.logger.error(f"AI client init failed: {e}")
            self.ai_client = None

    async def train_only_mode(self):
        self.logger.info("Training Mode Activated")
        try:
            self.training_data_generator.generate_and_store_all(synthetic_count=300, trade_log_limit=500, mode="default")
            if self.rl_trainer:
                self.rl_trainer.train()
            if self.genetic_optimizer:
                best = self.genetic_optimizer.run_optimization()
                if best:
                    self.logger.info(f"Best GA parameters: {best}")
            if self.feature_writer:
                feature = self.feature_writer.load_feature("sample_feature")
                if feature:
                    data = self.training_data_generator.get_samples_by_tag("default")
                    self.feature_writer.evaluate_feature(feature, data)
        except Exception as e:
            self.logger.error(f"Training error: {e}")
        self.logger.info("Training Mode Complete")

    def _train_only_sync(self):
        asyncio.run(self.train_only_mode())

    def initialize_modules(self):
        self.logger.info("Modules initialized via dashboard/API")
        self._init_ai_client()
        self.rl_trainer.reload_model()

agent = TradingAgent()

@api_app.get("/stats")
def get_stats():
    return agent.stats_tracker.get_latest()

@api_app.get("/stats/raw")
def get_raw_stats():
    return agent.stats_tracker.get_raw()

@api_app.post("/train")
def trigger_training():
    asyncio.create_task(agent.train_only_mode())
    return {"status": "Training started"}

@api_app.post("/reload-model")
def reload_model():
    try:
        agent.rl_trainer.reload_model()
        return {"status": "Model reloaded"}
    except Exception as e:
        return {"error": str(e)}

@api_app.post("/checkpoint")
def save_checkpoint():
    try:
        agent.rl_trainer.save_checkpoint()
        return {"status": "Checkpoint saved"}
    except Exception as e:
        return {"error": str(e)}

@api_app.post("/initialize")
def initialize_modules():
    try:
        agent.initialize_modules()
        return {"status": "Modules initialized"}
    except Exception as e:
        return {"error": str(e)}

async def main():
    config = uvicorn.Config(api_app, host="0.0.0.0", port=8081, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    print("Main has begun...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("AI Trading agent stopped by user.")
    except Exception as e:
        print(f"Error Encountered: {e}")
        logging.exception("Unhandled exception")

