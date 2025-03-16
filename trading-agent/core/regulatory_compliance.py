import logging
from datetime import datetime

logging.basicConfig(
    filename='logs/regulatory_compliance.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class RegulatoryCompliance:
    def __init__(self):
        self.daily_trade_count = 0
        self.max_daily_trades = 100  # Example rule for pattern day trading (PDT)

    def check_compliance(self):
        current_hour = datetime.now().hour
        if self.daily_trade_count > self.max_daily_trades:
            logging.error("Compliance violation: Exceeded daily trade limit.")
            return False
        if current_hour < 9 or current_hour > 16:
            logging.error("Compliance violation: Trading attempted outside allowed hours.")
            return False
        logging.info("Compliance check passed.")
        return True

    def increment_trade_count(self):
        self.daily_trade_count += 1
        logging.info(f"Trade count incremented: {self.daily_trade_count} trades today.")

    def reset_trade_count(self):
        self.daily_trade_count = 0
        logging.info("Daily trade count reset.")

