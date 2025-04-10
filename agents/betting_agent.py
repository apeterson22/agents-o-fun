from core.agent_registry import register_agent
import logging
import time
import random

@register_agent("betting", description="Sports and betting odds analysis", model="LLM", data_source="betting_lines, sports_feeds")
class BettingAgent:
    def __init__(self):
        self.status = "initialized"
        self.logger = logging.getLogger("betting")
        self.metadata = {
            "description": "Sports and betting odds analysis",
            "model": "LLM",
            "data_source": "betting_lines, sports_feeds"
        }
        # Parameters for advanced betting logic
        self.bet_threshold = 1.5  # Minimum odds threshold to consider placing a bet
        self.simulated_events = ["event1", "event2", "event3"]
        self.bet_interval = 30  # Time (in seconds) between betting cycles
        
        # Risk management and simulation parameters
        self.account_balance = 1000.0    # Starting balance in dollars
        self.total_bets = 0
        self.successful_bets = 0
        self.failed_bets = 0
        self.bet_success_rate = 0.66     # Base success probability for simulation

    def run(self):
        """Run the advanced betting logic cycle with risk management."""
        self.status = "running"
        self.logger.info("[BETTING AGENT] Starting advanced betting data collection and risk-managed analysis...")
        while self.status == "running":
            for event in self.simulated_events:
                try:
                    odds = self.fetch_betting_odds(event)
                    decision, bet_type, amount = self.analyze_betting_strategy(odds)
                    if decision:
                        if self.account_balance >= amount:
                            result = self.place_bet(event, bet_type, amount, odds)
                            self.logger.info(f"[BETTING AGENT] {result} | New balance: ${self.account_balance:.2f}")
                        else:
                            self.logger.warning(f"[BETTING AGENT] Insufficient funds for {event}: Bet amount ${amount} exceeds balance ${self.account_balance:.2f}")
                    else:
                        self.logger.info(f"[BETTING AGENT] No favorable betting opportunity for {event}. Odds: {odds:.2f}")
                except Exception as e:
                    self.failed_bets += 1
                    self.logger.error(f"[BETTING AGENT] Error processing event {event}: {e}")
                finally:
                    self.total_bets += 1
            self.logger.info("[BETTING AGENT] Completed betting cycle. Sleeping until next cycle...")
            time.sleep(self.bet_interval)

    def fetch_betting_odds(self, event_id):
        """
        Simulate fetching betting odds.
        This method can later be extended to integrate with a real betting API.
        """
        simulated_odds = random.uniform(1.0, 3.0)
        self.logger.info(f"[BETTING AGENT] Fetched odds for {event_id}: {simulated_odds:.2f}")
        return simulated_odds

    def analyze_betting_strategy(self, odds):
        """
        Advanced betting strategy:
          - If odds exceed the threshold, decide to place a 'back' bet.
          - Calculate bet amount based on how much the odds exceed the threshold.
        """
        if odds > self.bet_threshold:
            # Example: bet amount increases linearly with odds above threshold
            amount = round(100 * (odds - self.bet_threshold), 2)
            self.logger.info(f"[BETTING AGENT] Decision: Odds {odds:.2f} exceed threshold {self.bet_threshold}. Calculated bet amount: ${amount}")
            return True, "back", amount
        else:
            return False, None, 0

    def place_bet(self, event_id, bet_type, amount, odds):
        """
        Simulate placing a bet.
        Updates the account balance based on the simulated outcome.
        
        On a win, profit is calculated as bet amount * (odds - 1). On a loss, the bet amount is lost.
        """
        # Simulate success based on a defined probability
        success = random.random() < self.bet_success_rate
        if success:
            profit = round(amount * (odds - 1), 2)
            self.account_balance += profit
            self.successful_bets += 1
            return f"Success: {bet_type} bet of ${amount} placed on {event_id} won (profit: ${profit})."
        else:
            self.account_balance -= amount
            self.failed_bets += 1
            raise Exception(f"Bet placement failed for {event_id}. Lost ${amount}.")

    def stop(self):
        """Stop the agent's operation."""
        self.status = "stopped"
        self.logger.info("[BETTING AGENT] Agent stopped.")

    def health_check(self):
        """Return the current health status of the agent."""
        return {
            "status": self.status,
            "uptime": "TODO: add uptime tracking",
            "last_error": None,
            "account_balance": self.account_balance
        }

    def get_metrics(self):
        """Provide detailed simulated metrics for the betting agent."""
        error_rate = (self.failed_bets / self.total_bets) if self.total_bets > 0 else 0
        return {
            "total_bets": self.total_bets,
            "successful_bets": self.successful_bets,
            "failed_bets": self.failed_bets,
            "error_rate": round(error_rate, 2),
            "current_balance": round(self.account_balance, 2)
        }

