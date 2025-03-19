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
import requests
from dotenv import load_dotenv
import sys

##################################
### Needed for troubleshooting ###
##################################
sys.setrecursionlimit(10000)

logging.basicConfig(
    filename='logs/main_agent.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    filemode='a',
    force=True  # forces immediate setup
)
logging.info("Logging successfully initialized.")
print("Script Started, logging initialing")
logging.info("Script started correctly.")

try:
    # Quick modules check
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

###################################
###  End of troubleshooting     ###
###################################
load_dotenv()  # Load environment variables from .env file

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
        self.load_config(config_file)
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

        self.daily_goal = self.config.getfloat('Goals', 'daily_profit')  # Ensures daily_goal is initialized
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
        
        self.ai_provider = self.config.get('AI', 'provider')
        self.ai_endpoint = self.config.get('AI', 'endpoint')
        self.ai_api_key = os.getenv("AI_API_KEY", self.config.get('AI', 'api_key', fallback=None))
        self._init_ai_client()

        self.dashboard = MonitoringDashboard(agent=self)
        self.dashboard.integrate_components(self.rl_trainer, self.genetic_optimizer, self.feature_writer)
        threading.Thread(target=self.dashboard.start, daemon=True).start()

    def train_only_mode(self) -> None:
        """Runs the agent in training mode only, without executing trades."""
        self.logger.info("Training Mode Activated: Running AI Training...")

        # Run Reinforcement Learning Training
        if self.rl_trainer:
            self.logger.info("Running RL Training...")
            self.rl_trainer.train_model(timesteps=10000)

        # Run Genetic Algorithm Optimization
        if self.genetic_optimizer:
            self.logger.info("Running Genetic Algorithm Optimization...")
            best_params = self.genetic_optimizer.run_optimization()
            if best_params:
                self.logger.info(f"Optimized parameters found: {best_params}")

        # Run Feature Engineering
        if self.feature_writer:
            self.logger.info("Running Feature Engineering...")
            if hasattr(self.feature_writer, "evaluate_feature"):
                self.logger.info("Running Feature Evaluation...")
                sample_module = self.feature_writer.load_feature("sample_feature")  # Change this if needed
                sample_data = [{"expected_return": 100}, {"expected_return": -50}]
                if sample_module:
                    self.feature_writer.evaluate_feature(sample_module, sample_data)
            elif hasattr(self.feature_writer, "continuous_evaluation_cycle"):
                self.logger.info("Running Continuous Evaluation Cycle...")
                sample_data = [{"expected_return": 100}, {"expected_return": -50}]
                threading.Thread(target=self.feature_writer.continuous_evaluation_cycle, args=(sample_data, 3600), daemon=True).start()
            else:
                self.logger.error("Feature writer has no valid method for training mode.")
#            if hasattr(self.feature_writer, "evaluate_and_write"):
#                self.feature_writer.evaluate_and_write()
#            elif hasattr(self.feature_writer, "process_features"):  # Example alternative
#                self.feature_writer.process_features()
#            else:
#                self.logger.error("Feature writer has no valid method for training mode.")

        self.logger.info("Training Mode Complete.")


    def load_config(self, config_file: str) -> configparser.ConfigParser:
        """Loads the configuration from the specified file."""
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
        self.logger.info(f"Configuration loaded: Daily Goal = ${self.daily_goal:,}")

    def _init_ai_client(self) -> None:
        print("Starting Ai Client init...")
        try:
            if self.ai_provider.lower() == 'ollama':
                from ollama import Client
                self.ai_client = Client(host=self.ai_endpoint)  # External server endpoint
                # Test connection
                response = requests.get(f"{self.ai_endpoint}/api/tags", timeout=5)
                if response.status_code != 200:
                    raise ConnectionError("Ollama server not reachable")
                self.logger.info(f"Initialized Ollama client to external server at {self.ai_endpoint}")
            elif self.ai_provider.lower() == 'openai':
                self.ai_client = lambda prompt: requests.post(
                    "https://api.openai.com/v1/completions",
                    headers={"Authorization": f"Bearer {self.ai_api_key}"},
                    json={"model": "text-davinci-003", "prompt": prompt, "max_tokens": 500}
                ).json()
                self.logger.info("Initialized OpenAI client")
            elif self.ai_provider.lower() == 'grok':
                self.ai_client = lambda prompt: requests.post(
                    "https://api.x.ai/v1/grok",  # Hypothetical endpoint
                    headers={"Authorization": f"Bearer {self.ai_api_key}"},
                    json={"prompt": prompt}
                ).json()
                self.logger.info("Initialized Grok client")
            else:
                raise ValueError(f"Unsupported AI provider: {self.ai_provider}")
        except Exception as e:
            self.logger.error(f"AI client initialization failed: {e}")
            self.ai_client = None

    async def trading_loop(self) -> None:
        while True:
            try:
                if not await self.health_check():
                    self.logger.error("System health check failed. Trading halted.")
                    self.logger.info("Switching to Training Mode.")
                    self.train_only_mode()  # Ensure training continues
                    await asyncio.sleep(300)  # Wait and retry health check
                    continue  # Skip trading 

                current_date = datetime.now().date()
                if current_date > self.last_reset:
                    self.daily_profit = 0.0
                    self.last_reset = current_date
                    self.logger.info("Daily profit reset for new trading day")
                    current_hour = datetime.now().hour
                if self.compliance.check_compliance():
                    logging.info("Within trading hours. Running trading cycle...")
                    print("Trading is active...")
                    stock_data = await self._fetch_with_retry(self.fidelity_api.get_market_data, {"symbol": "PENNY_STOCKS"})
                    crypto_data = await self._fetch_with_retry(self.crypto_api.get_coinbase_data, {"symbol": "BTC-USD"})
                    betting_data = await self._fetch_with_retry(self.betting_api.get_betting_odds, {"event_id": "EVENT_ID"})
                    trades, bets = self.trading_engine.evaluate_strategies(stock_data, crypto_data, betting_data)
                    self.trading_engine.execute_trades_and_bets(trades, bets)
                else:
                    logging.info("Outside trading hours. Running analysis & training.")
                    self.train_only_mode()  # Ensure training runs
                    self.rl_trainer.train_model(10000)
                    self.genetic_optimizer.run_optimization()
                    self.feature_writer.evaluate_and_write()

                await asyncio.sleep(300)  # 5-minute sleep intervals
            except Exception as e:
                self.logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(60)

    async def _fetch_with_retry(self, func, kwargs: Dict, retries: int = 3, delay: int = 5) -> Optional[Dict]:
        for attempt in range(retries):
            try:
                return await asyncio.ensure_future(func(**kwargs))
            except Exception as e:
                self.logger.warning(f"API fetch failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (2 ** attempt))
        self.logger.error(f"Failed to fetch data after {retries} attempts")
        return {}

    async def _execute_and_monitor(self, trades: List, bets: List) -> List[Dict]:
        executed_trades = self.trading_engine.execute_trades_and_bets(trades, bets)
        for trade in executed_trades:
            if 'profit' in trade:
                self.daily_profit += trade['profit']
                trade['source'] = trade.get('market', 'unknown')
                self.dashboard.add_trade_record(trade)
        return executed_trades

    async def _ai_enhanced_evaluation(self, stock_data: Dict, crypto_data: Dict, betting_data: Dict) -> Tuple[List, List]:
        trades, bets = self.trading_engine.evaluate_strategies(stock_data, crypto_data, betting_data)
        if self.ai_client:
            prompt = (
                f"Market data:\nStocks: {stock_data}\nCrypto: {crypto_data}\nBetting: {betting_data}\n"
                f"Trades: {trades}\nBets: {bets}\nSuggest adjustments for $10,000 daily profit."
            )
            try:
                if self.ai_provider.lower() == 'ollama':
                    response = await asyncio.get_event_loop().run_in_executor(
                        self.executor, lambda: self.ai_client.generate(model='llama2', prompt=prompt)
                    )
                    ai_suggestions = response.get('response', [])
                else:
                    response = await asyncio.get_event_loop().run_in_executor(
                        self.executor, lambda: self.ai_client(prompt)
                    )
                    ai_suggestions = response.get('choices', [{}])[0].get('text', '')
                adjustments = json.loads(ai_suggestions) if isinstance(ai_suggestions, str) else ai_suggestions
                trades.extend([t for t in adjustments if 'market' in t and t['market'] != 'sports'])
                bets.extend([b for b in adjustments if 'market' in b and b['market'] == 'sports'])
            except Exception as e:
                self.logger.error(f"AI evaluation failed: {e}")
        return trades, bets

    async def _self_improve(self, stock_data: Dict, crypto_data: Dict, betting_data: Dict, trades: List[Dict]) -> None:
        if not hasattr(self, '_feature_thread'):
            self._feature_thread = threading.Thread(
                target=self.feature_writer.continuous_evaluation_cycle,
                args=(trades, 300),
                daemon=True
            )
            self._feature_thread.start()

        if self.rl_trainer:
            self.rl_trainer.train_model(timesteps=10000)
            model = self.rl_trainer.load_model()
            if model:
                rl_trade = {'market': 'crypto', 'profit': 50, 'strategy': 'ppo_rl', 'trade_type': 'buy', 'source': 'RLTrainer'}
                self.dashboard.add_trade_record(rl_trade)

        if self.genetic_optimizer:
            best_params = self.genetic_optimizer.run_optimization()
            if best_params:
                self.logger.info(f"New optimized parameters: {best_params}")

        dynamic_feature = self.feature_writer.load_feature("dynamic_trading_feature")
        if dynamic_feature:
            additional_trades = dynamic_feature.new_strategy(stock_data)
            await self._execute_and_monitor(additional_trades, [])

    async def health_check(self) -> bool:
        try:
            apis_ok = all(
                api.is_healthy() for api in [self.fidelity_api, self.crypto_api, self.betting_api]
                if hasattr(api, 'is_healthy')
            )
            compliance_ok = self.compliance.check_compliance()
            ai_ok = self.ai_client is not None
            if not apis_ok:
                self.logger.error("Health Check Failed: One or more APIs are unavailable.")
            if not compliance_ok:
                self.logger.error("Health Check Failed: Compliance check did not pass.")
            if not ai_ok:
                self.logger.error("Health Check Failed: AI Client is not initialized.")
            return apis_ok and compliance_ok and ai_ok
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

async def main() -> None:
    agent = TradingAgent()
    await agent.trading_loop()

if __name__ == "__main__":
    print("Main has begun...")
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("AI Trading agent stopped by user.")
    except Exception as e:
        print(f"Error Encountered: {e}")
        logging.exception(f"Unhandled exception: {e}")
        logging.error(f"Main execution failed: {e}")
