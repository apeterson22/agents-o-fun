import logging
from datetime import datetime

logging.basicConfig(filename='logs/regulatory_compliance.log', level=logging.INFO)

class RegulatoryCompliance:
    def __init__(self, trading_start=9, trading_end=16, max_trades_per_day=100):
        self.trading_start = trading_start
        self.trading_end = trading_end
        self.daily_trade_count = 0
        self.max_daily_trades = max_trades_per_day

    def check_compliance(self):
        current_hour = datetime.now().hour
        if not (self.trading_start <= current_hour <= self.trading_end):
            logging.warning("Outside trading hours.")
            return False
        if self.daily_trade_count >= self.max_daily_trades:
            logging.warning("Daily trade limit exceeded.")
            return False
        return True

    def increment_trade_count(self):
        self.daily_trade_count += 1
        logging.info(f"Trade count incremented: {self.daily_trade_count}")

    def reset_trade_count(self):
        self.daily_trade_count = 0
        logging.info("Daily trade count reset.")

