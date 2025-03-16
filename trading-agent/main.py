import asyncio
import logging
import threading
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
import os
import configparser
from core.api_interface import FidelityAPI
from core.crypto_interface import CryptoAPI
from core.betting_interface import BettingAPI
from core.trading_engine import TradingEngine
from core.risk_manager import RiskManager
from core.regulatory_compliance import RegulatoryCompliance
from ai_self_improvement.feature_writer import AdvancedFeatureWriter
from dashboards.monitoring import MonitoringDashboard
from ai_self_improvement.rl_trainer import RLTrainer
from ai_self_improvement.genetic_optimizer import GeneticOptimizer
import requests  # For AI API calls
from ollama import Client as OllamaClient  # Assuming ollama Python client exists

def setup_logging(log_file: str = 'logs/main_agent.log') -> logging.Logger:
    """Configure logging with detailed format."""
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
        """Initialize the trading agent with all components and configuration."""
        self.logger = setup_logging()
        self.load_config(config_file)
        
        # Daily profit tracking
        self.daily_profit = 0.0
        self.last_reset = datetime.now().date()
        
        # API Initialization with error handling
        try:
            self.fidelity_api = FidelityAPI(api_key=os.getenv("FIDELITY_API_KEY", self.config.get('API', 'fidelity_key', fallback="Fidelity_API_KEY")))
            self.crypto_api = CryptoAPI(
                coinbase_api_key=os.getenv("COINBASE_KEY", self.config.get('API', 'coinbase_key', fallback="COINBASE_KEY")),
                cryptocom_api_key=os.getenv("CRYPTOCOM_KEY", self.config.get('API', 'cryptocom_key', fallback="CRYPTOCOM_KEY"))
            )
            self.betting_api = BettingAPI(cryptocom_api_key=os.getenv("CRYPTOCOM_BETTING_KEY", self.config.get('API', 'cryptocom_betting_key', fallback="CRYPTOCOM_BETTING_KEY")))
        except Exception as e:
            self.logger.error(f"API initialization failed: {e}")
            raise

        # Core Components
        self.risk_manager = RiskManager(
            max_daily_loss=self.config.getfloat('Risk', 'max_daily_loss', fallback=5000),
            stop_loss_pct=self.config.getfloat('Risk', 'stop_loss_pct', fallback=0.03),
            max_position_size=self.config.getfloat('Risk', 'max_position_size', fallback=2000),
            daily_goal=self.daily_goal
        )
        self.compliance = RegulatoryCompliance()
        self.trading_engine = TradingEngine(
            fidelity_api=self.fidelity_api,
            crypto_api=self.crypto_api,
            betting_api=self.betting_api,
            risk_manager=self.risk_manager,
            compliance=self.compliance
        )

        # AI Components
        self.feature_writer = AdvancedFeatureWriter()
        self.rl_trainer = RLTrainer()
        self.genetic_optimizer = GeneticOptimizer()
        
        # AI Integration (Ollama or Third-Party)
        self.ai_provider = self.config.get('AI', 'provider', fallback='ollama')
        self.ai_endpoint = self.config.get('AI', 'endpoint', fallback='http://localhost:11434')  # Default Ollama local
        self.ai_api_key = os.getenv("AI_API_KEY", self.config.get('AI', 'api_key', fallback=None))
        self._init_ai_client()

        # Dashboard
        self.dashboard = MonitoringDashboard()
        self.dashboard.integrate_components(self.rl_trainer, self.genetic_optimizer, self.feature_writer)
        threading.Thread(target=self.dashboard.start, daemon=True).start()

    def load_config(self, config_file: str) -> None:
        """Load configuration from file."""
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.daily_goal = self.config.getfloat('Goals', 'daily_profit', fallback=10000)
        self.logger.info(f"Configuration loaded: Daily Goal = ${self.daily_goal:,}")

    def _init_ai_client(self) -> None:
        """Initialize AI client based on provider."""
        try:
            if self.ai_provider.lower() == 'ollama':
                self.ai_client = OllamaClient(host=self.ai_endpoint)
                self.logger.info(f"Initialized local Ollama AI at {self.ai_endpoint}")
            elif self.ai_provider.lower() == 'openai':
                self.ai_client = lambda prompt: requests.post(
                    "https://api.openai.com/v1/completions",
                    headers={"Authorization": f"Bearer {self.ai_api_key}"},
                    json={"model": "text-davinci-003", "prompt": prompt, "max_tokens": 500}
                ).json()
                self.logger.info("Initialized OpenAI client")
            elif self.ai_provider.lower() == 'grok':
                self.ai_client = lambda prompt: requests.post(
                    "https://api.xai.com/v1/grok",  # Hypothetical endpoint
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
        """Main trading loop with enhanced logic."""
        while True:
            try:
                if not await self.health_check():
                    self.logger.error("System health check failed. Trading halted.")
                    break

                # Reset daily profit tracking if new day
                current_date = datetime.now().date()
                if current_date > self.last_reset:
                    self.daily_profit = 0.0
                    self.last_reset = current_date
                    self.logger.info("Daily profit reset for new trading day")

                # Fetch market data
                stock_data = await self._fetch_with_retry(self.fidelity_api.get_market_data, {"symbol": "PENNY_STOCKS"})
                crypto_data = await self._fetch_with_retry(self.crypto_api.get_coinbase_data, {"symbol": "BTC-USD"})
                betting_data = await self._fetch_with_retry(self.betting_api.get_betting_odds, {"event_id": "EVENT_ID"})

                # AI-enhanced strategy evaluation
                trades, bets = await self._ai_enhanced_evaluation(stock_data, crypto_data, betting_data)
                executed_trades = await self._execute_and_monitor(trades, bets)

                # Self-improvement cycle
                await self._self_improve(stock_data, crypto_data, betting_data, executed_trades)

                # Check progress towards daily goal
                if self.daily_profit >= self.daily_goal:
                    self.logger.info(f"Daily profit goal of ${self.daily_goal:,} achieved: ${self.daily_profit:,.2f}")
                    await asyncio.sleep(3600)  # Pause for an hour
                else:
                    await asyncio.sleep(5)  # Normal trading interval

            except Exception as e:
                self.logger.error(f"Trading loop error: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _fetch_with_retry(self, func, kwargs: Dict, retries: int = 3, delay: int = 5) -> Optional[Dict]:
        """Fetch data with retry logic."""
        for attempt in range(retries):
            try:
                return await asyncio.ensure_future(func(**kwargs))
            except Exception as e:
                self.logger.warning(f"API fetch failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
        self.logger.error(f"Failed to fetch data after {retries} attempts")
        return {}

    async def _execute_and_monitor(self, trades: List, bets: List) -> List[Dict]:
        """Execute trades/bets and update dashboard."""
        executed_trades = self.trading_engine.execute_trades_and_bets(trades, bets)
        for trade in executed_trades:
            if 'profit' in trade:
                self.daily_profit += trade['profit']
                trade['source'] = trade.get('market', 'unknown')
                self.dashboard.add_trade_record(trade)
        return executed_trades

    async def _ai_enhanced_evaluation(self, stock_data: Dict, crypto_data: Dict, betting_data: Dict) -> Tuple[List, List]:
        """Evaluate strategies with AI assistance."""
        trades, bets = self.trading_engine.evaluate_strategies(stock_data, crypto_data, betting_data)
        if self.ai_client:
            try:
                prompt = (
                    f"Given market data:\nStocks: {stock_data}\nCrypto: {crypto_data}\nBetting: {betting_data}\n"
                    f"Current trades: {trades}\nBets: {bets}\n"
                    "Suggest improvements to maximize daily profit ($10,000 goal). Return a list of trade/bet adjustments."
                )
                if self.ai_provider.lower() == 'ollama':
                    response = self.ai_client.generate(model='llama2', prompt=prompt)
                    ai_suggestions = response.get('response', [])
                else:  # OpenAI or Grok
                    response = self.ai_client(prompt)
                    ai_suggestions = response.get('choices', [{}])[0].get('text', '')

                # Parse AI suggestions (assuming JSON-like list response)
                try:
                    import json
                    adjustments = json.loads(ai_suggestions) if isinstance(ai_suggestions, str) else ai_suggestions
                    trades.extend([t for t in adjustments if 'market' in t and t['market'] != 'sports'])
                    bets.extend([b for b in adjustments if 'market' in b and b['market'] == 'sports'])
                except Exception as e:
                    self.logger.warning(f"Failed to parse AI suggestions: {e}")
            except Exception as e:
                self.logger.error(f"AI evaluation failed: {e}")
        return trades, bets

    async def _self_improve(self, stock_data: Dict, crypto_data: Dict, betting_data: Dict, trades: List[Dict]) -> None:
        """Run self-improvement cycle with all AI components."""
        # Feature Writer (in background)
        threading.Thread(
            target=self.feature_writer.continuous_evaluation_cycle,
            args=(trades, 300),  # 5-minute interval
            daemon=True
        ).start()

        # RL Trainer
        if self.rl_trainer:
            self.rl_trainer.train_model(timesteps=10000)
            model = self.rl_trainer.load_model()
            if model:
                rl_trade = {'market': 'crypto', 'profit': 50, 'strategy': 'ppo_rl', 'trade_type': 'buy', 'source': 'RLTrainer'}
                self.dashboard.add_trade_record(rl_trade)

        # Genetic Optimizer
        if self.genetic_optimizer:
            best_params = self.genetic_optimizer.run_optimization()
            if best_params:
                self.logger.info(f"New optimized parameters: {best_params}")

        # Dynamic Feature Integration
        dynamic_feature = self.feature_writer.load_feature("dynamic_trading_feature")
        if dynamic_feature:
            additional_trades = dynamic_feature.new_strategy(stock_data)
            await self._execute_and_monitor(additional_trades, [])

    async def health_check(self) -> bool:
        """Check system health."""
        try:
            apis_ok = all(
                api.is_healthy() for api in [self.fidelity_api, self.crypto_api, self.betting_api]
                if hasattr(api, 'is_healthy')
            )
            compliance_ok = self.compliance.check_compliance()
            ai_ok = self.ai_client is not None
            if not apis_ok:
                self.logger.warning("One or more APIs are unhealthy")
            if not compliance_ok:
                self.logger.warning("Compliance check failed")
            if not ai_ok:
                self.logger.warning("AI client is not available")
            return apis_ok and compliance_ok and ai_ok
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False

async def main() -> None:
    """Main entry point for the trading agent."""
    agent = TradingAgent()
    await agent.trading_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("AI Trading agent stopped by user.")
    except Exception as e:
        logging.error(f"Main execution failed: {e}")
