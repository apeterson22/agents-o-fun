import logging
from strategies import momentum, scalping, arbitrage, crypto_trading, betting_strategy

logging.basicConfig(
    filename='logs/trading_engine.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class TradingEngine:
    def __init__(self, fidelity_api, crypto_api, betting_api, risk_manager, compliance):
        """
        Initialize the TradingEngine with the required API interfaces,
        risk manager, and regulatory compliance module.
        
        Parameters:
            fidelity_api: Interface for traditional market orders.
            crypto_api: Interface for cryptocurrency orders.
            betting_api: Interface for placing bets.
            risk_manager: Instance of the RiskManager.
            compliance: Instance of the RegulatoryCompliance.
        """
        self.fidelity_api = fidelity_api
        self.crypto_api = crypto_api
        self.betting_api = betting_api
        self.risk_manager = risk_manager
        self.compliance = compliance

    def evaluate_strategies(self, stock_data, crypto_data, betting_data):
        """
        Evaluate a suite of trading strategies and betting signals.
        
        Parameters:
            stock_data: Historical or live stock market data.
            crypto_data: Historical or live cryptocurrency data.
            betting_data: Data for betting strategy evaluation.
            
        Returns:
            tuple: (trades, bets) lists containing trade signals and bet signals.
        """
        trades = []
        trades.extend(momentum.evaluate(stock_data))
        trades.extend(scalping.evaluate(stock_data))
        trades.extend(arbitrage.evaluate(stock_data))
        trades.extend(crypto_trading.evaluate(crypto_data))
        bets = betting_strategy.evaluate(betting_data)
        logging.info("Evaluated strategies: %d trades, %d bets identified.", len(trades), len(bets))
        return trades, bets

    def execute_trades_and_bets(self, trades, bets):
        """
        Execute trade and bet signals while checking risk and compliance.
        
        For each trade, the risk manager assesses the trade parameters.
        If compliant, the order is placed via the FidelityAPI.
        
        Bets are executed via the BettingAPI.
        """
        for trade in trades:
            if not self.compliance.check_compliance():
                logging.warning("Trade skipped due to compliance failure: %s", trade)
                continue
            if self.risk_manager.assess_trade_risk(trade['entry'], trade['stop_loss'], trade['size']):
                result = self.fidelity_api.place_order(trade['symbol'], trade['size'], trade['order_type'], trade['side'])
                if result:
                    # Update daily profit (if applicable) and trade count
                    self.risk_manager.update_daily_profit(trade.get('profit', 0))
                    self.compliance.increment_trade_count()
                    logging.info("Executed trade: %s", trade)
                else:
                    logging.error("Failed to execute trade via FidelityAPI: %s", trade)
            else:
                logging.warning("Trade skipped due to risk assessment failure: %s", trade)

        for bet in bets:
            result = self.betting_api.place_bet(bet['event_id'], bet['bet_type'], bet['amount'])
            if result:
                logging.info("Placed bet successfully: %s", bet)
            else:
                logging.warning("Failed to place bet: %s", bet)

    def run_engine(self, stock_data, crypto_data, betting_data):
        """
        Run the full trading engine process:
          - Evaluate strategies.
          - Execute approved trades and bets.
        """
        trades, bets = self.evaluate_strategies(stock_data, crypto_data, betting_data)
        self.execute_trades_and_bets(trades, bets)

