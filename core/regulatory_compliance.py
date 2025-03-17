import logging
from datetime import datetime

logging.basicConfig(
    filename='logs/regulatory_compliance.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class RegulatoryCompliance:
    def __init__(self, trading_start=9, trading_end=16):
        self.trading_start = trading_start
        self.trading_end = trading_end
        self.daily_trade_count = 0
        self.max_daily_trades = 100  # Example rule for pattern day trading (PDT)

    def check_compliance(self):
        current_hour = datetime.now().hour
        if self.trading_start <= current_hour <= self.trading_end:
            logging.info("Within trading hours. Trading permitted.")
            return True
        else:
            logging.warning("Outside trading hours. Trading halted; switching to analysis and training.")
            return False  # Clearly indicates outside trading hours
        if self.daily_trade_count > self.max_daily_trades:
            logging.error("Compliance violation: Exceeded daily trade limit.")
            return False
 #       if current_hour < 9 or current_hour > 16:
 #           logging.error("Compliance violation: Trading attempted outside allowed hours.")
 #           return False
        logging.info("Compliance check passed.")
        return True

    def increment_trade_count(self):
        self.daily_trade_count += 1
        logging.info(f"Trade count incremented: {self.daily_trade_count} trades today.")

    def reset_trade_count(self):
        self.daily_trade_count = 0
        logging.info("Daily trade count reset.")

