import logging

logging.basicConfig(
    filename='logs/risk_manager.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class RiskManager:
    def __init__(self, max_daily_loss, stop_loss_pct, max_position_size, daily_goal=10000):
        self.daily_goal = daily_goal
        self.max_daily_loss = max_daily_loss
        self.stop_loss_pct = stop_loss_pct
        self.max_position_size = max_position_size
        self.current_daily_loss = 0
        self.current_daily_profit = 0

    def assess_trade_risk(self, entry_price, stop_price, position_size):
        potential_loss = abs(entry_price - stop_price) * position_size
        if potential_loss + self.current_daily_loss > self.max_daily_loss:
            logging.warning("Trade rejected: Potential daily loss limit exceeded.")
            return False
        if position_size > self.max_position_size:
            logging.warning("Trade rejected: Position size limit exceeded.")
            return False
        logging.info("Trade approved by risk assessment.")
        return True

    def update_daily_loss(self, loss_amount):
        self.current_daily_loss += loss_amount
        logging.info(f"Daily loss updated: Current daily loss = {self.current_daily_loss}")

