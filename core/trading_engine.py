import logging
from strategies import momentum, scalping, arbitrage, crypto_trading, betting_strategy

logging.basicConfig(
    filename='logs/trading_engine.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class TradingEngine:
    def __init__(self, fidelity_api, crypto_api, betting_api, risk_manager, compliance):
        self.fidelity_api = fidelity_api
        self.crypto_api = crypto_api
        self.betting_api = betting_api
        self.risk_manager = risk_manager
        self.compliance = compliance

    def evaluate_strategies(self, stock_data, crypto_data, betting_data):
        trades = []
        trades.extend(momentum.evaluate(stock_data))
        trades.extend(scalping.evaluate(stock_data))
        trades.extend(arbitrage.evaluate(stock_data))
        trades.extend(crypto_trading.evaluate(crypto_data))
        bets = betting_strategy.evaluate(betting_data)
        logging.info(f"Evaluated strategies: {len(trades)} trades, {len(bets)} bets identified.")
        return trades, bets

    def execute_trades_and_bets(self, trades, bets):
        for trade in trades:
            if self.risk_manager.assess_trade_risk(trade['entry'], trade['stop_loss'], trade['size']):
                result = self.fidelity_api.place_order(trade['symbol'], trade['size'], trade['order_type'], trade['side'])
                if result:
                    self.compliance.increment_trade_count()
                    logging.info(f"Executed trade: {trade}")
            else:
                logging.warning(f"Skipped trade due to risk assessment: {trade}")

        for bet in bets:
            result = self.betting_api.place_bet(bet['event_id'], bet['bet_type'], bet['amount'])
            if result:
                logging.info(f"Placed bet successfully: {bet}")
            else:
                logging.warning(f"Failed to place bet: {bet}")

