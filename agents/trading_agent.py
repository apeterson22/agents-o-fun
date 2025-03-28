from core.api_interface import FidelityAPI
from core.crypto_interface import CryptoAPI
from core.betting_interface import BettingAPI
from core.risk_manager import RiskManager
from core.regulatory_compliance import RegulatoryCompliance
from core.trading_engine import TradingEngine
from core.agent_registry import register_agent

@register_agent("trading")
class TradingAgent:
    def run(self):
        fidelity = FidelityAPI(api_key="demo-key")
        crypto = CryptoAPI("coinbase-key", "cryptocom-key")
        betting = BettingAPI("cryptocom-key")
        risk = RiskManager(max_daily_loss=5000, stop_loss_pct=0.05, max_position_size=100)
        compliance = RegulatoryCompliance()
        engine = TradingEngine(fidelity, crypto, betting, risk, compliance)

        stock_data, crypto_data, betting_data = {}, {}, {}
        trades, bets = engine.evaluate_strategies(stock_data, crypto_data, betting_data)
        engine.execute_trades_and_bets(trades, bets)

