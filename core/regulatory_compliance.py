import logging
from datetime import datetime

logging.basicConfig(filename='logs/regulatory_compliance.log', level=logging.INFO,
                    format='%(asctime)s [%(levelname)s]: %(message)s')

class RegulatoryCompliance:
    def __init__(self, trading_start=9, trading_end=16, max_trades_per_day=100):
        """
        Initialize RegulatoryCompliance with trading hours and maximum trades per day.
        
        Parameters:
            trading_start (int): Trading start hour (24h format).
            trading_end (int): Trading end hour (24h format).
            max_trades_per_day (int): Maximum number of trades allowed per day.
        """
        self.trading_start = trading_start
        self.trading_end = trading_end
        self.daily_trade_count = 0
        self.max_daily_trades = max_trades_per_day
        self.last_reset_date = datetime.now().date()

    def reset_trade_count_if_new_day(self):
        """Reset the daily trade count if a new day has started."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            logging.info("Resetting daily trade count. Previous count: %d", self.daily_trade_count)
            self.daily_trade_count = 0
            self.last_reset_date = today

    def check_compliance(self):
        """
        Check if current trading conditions are compliant.
        Verifies trading hours and that the daily trade limit has not been exceeded.
        
        Returns:
            bool: True if compliant; False otherwise.
        """
        self.reset_trade_count_if_new_day()
        current_hour = datetime.now().hour
        if not (self.trading_start <= current_hour < self.trading_end):
            logging.warning("Compliance check failed: Outside trading hours (Current: %d, Allowed: %d-%d)",
                            current_hour, self.trading_start, self.trading_end)
            return False
        if self.daily_trade_count >= self.max_daily_trades:
            logging.warning("Compliance check failed: Daily trade limit exceeded (%d/%d)",
                            self.daily_trade_count, self.max_daily_trades)
            return False
        return True

    def increment_trade_count(self):
        """Increment the daily trade count and log the update."""
        self.reset_trade_count_if_new_day()
        self.daily_trade_count += 1
        logging.info("Trade count incremented: %d", self.daily_trade_count)

    def reset_trade_count(self):
        """Reset the daily trade count and log the reset."""
        logging.info("Daily trade count reset. Previous count: %d", self.daily_trade_count)
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()

    def compliance_summary(self):
        """
        Return a summary of the compliance status for monitoring.
        
        Returns:
            dict: Summary including trading hours, current trade count, and compliance status.
        """
        self.reset_trade_count_if_new_day()
        summary = {
            "trading_hours": f"{self.trading_start}:00 - {self.trading_end}:00",
            "daily_trade_count": self.daily_trade_count,
            "max_daily_trades": self.max_daily_trades,
            "within_trading_hours": self.trading_start <= datetime.now().hour < self.trading_end,
            "compliant": self.check_compliance()
        }
        logging.info("Compliance summary: %s", summary)
        return summary

