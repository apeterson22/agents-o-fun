import logging
from datetime import datetime

logging.basicConfig(
    filename='logs/risk_manager.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class RiskManager:
    def __init__(self, max_daily_loss, stop_loss_pct, max_position_size, daily_goal=10000):
        """
        Initialize the RiskManager.

        Parameters:
            max_daily_loss (float): Maximum allowable loss per day.
            stop_loss_pct (float): Percentage (as a decimal) used to calculate stop loss from entry price.
            max_position_size (float): Maximum allowed size of any trade position.
            daily_goal (float): Daily profit target.
        """
        self.daily_goal = daily_goal
        self.max_daily_loss = max_daily_loss
        self.stop_loss_pct = stop_loss_pct
        self.max_position_size = max_position_size
        self.current_daily_loss = 0
        self.current_daily_profit = 0
        self.last_reset_date = datetime.now().date()

    def reset_daily_counters(self):
        """Reset daily profit and loss counters if a new day has started."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            logging.info("Resetting daily risk counters. Previous profit: %.2f, loss: %.2f",
                         self.current_daily_profit, self.current_daily_loss)
            self.current_daily_loss = 0
            self.current_daily_profit = 0
            self.last_reset_date = today

    def assess_trade_risk(self, entry_price, stop_price, position_size):
        """
        Assess whether a trade is within acceptable risk limits.

        Parameters:
            entry_price (float): The trade entry price.
            stop_price (float): The designated stop loss price.
            position_size (float): The size of the trade position.

        Returns:
            bool: True if the trade is approved; otherwise, False.
        """
        self.reset_daily_counters()
        potential_loss = abs(entry_price - stop_price) * position_size
        if potential_loss + self.current_daily_loss > self.max_daily_loss:
            logging.warning("Trade rejected: Potential loss %.2f with current daily loss %.2f exceeds max daily loss %.2f.",
                            potential_loss, self.current_daily_loss, self.max_daily_loss)
            return False
        if position_size > self.max_position_size:
            logging.warning("Trade rejected: Position size %.2f exceeds maximum allowed %.2f.", position_size, self.max_position_size)
            return False
        logging.info("Trade approved: Potential loss %.2f, Position size %.2f.", potential_loss, position_size)
        return True

    def update_daily_loss(self, loss_amount):
        """
        Update the current daily loss total.

        Parameters:
            loss_amount (float): The loss incurred from a trade.
        """
        self.reset_daily_counters()
        self.current_daily_loss += loss_amount
        logging.info("Daily loss updated: Current daily loss = %.2f", self.current_daily_loss)

    def update_daily_profit(self, profit_amount):
        """
        Update the current daily profit total.

        Parameters:
            profit_amount (float): The profit realized from a trade.
        """
        self.reset_daily_counters()
        self.current_daily_profit += profit_amount
        logging.info("Daily profit updated: Current daily profit = %.2f", self.current_daily_profit)

    def check_daily_goal(self):
        """
        Check if the daily profit goal has been met.

        Returns:
            bool: True if the current daily profit is at or above the goal; otherwise, False.
        """
        self.reset_daily_counters()
        if self.current_daily_profit >= self.daily_goal:
            logging.info("Daily goal achieved: Profit = %.2f, Goal = %.2f", self.current_daily_profit, self.daily_goal)
            return True
        logging.info("Daily goal not met: Profit = %.2f, Goal = %.2f", self.current_daily_profit, self.daily_goal)
        return False

    def calculate_stop_loss(self, entry_price):
        """
        Calculate the stop loss price based on the entry price and configured stop loss percentage.

        Parameters:
            entry_price (float): The trade entry price.

        Returns:
            float: The calculated stop loss price.
        """
        stop_loss = entry_price * (1 - self.stop_loss_pct)
        logging.info("Calculated stop loss: Entry Price = %.2f, Stop Loss = %.2f (%.2f%%)", 
                     entry_price, stop_loss, self.stop_loss_pct * 100)
        return stop_loss

    def get_risk_metrics(self):
        """
        Retrieve current risk metrics for dashboard display or logging.

        Returns:
            dict: Dictionary containing current daily profit, loss, remaining risk capacity, and set goals.
        """
        self.reset_daily_counters()
        remaining_risk = self.max_daily_loss - self.current_daily_loss
        return {
            "current_daily_profit": self.current_daily_profit,
            "current_daily_loss": self.current_daily_loss,
            "remaining_risk_capacity": remaining_risk,
            "daily_goal": self.daily_goal,
            "max_daily_loss": self.max_daily_loss
        }

