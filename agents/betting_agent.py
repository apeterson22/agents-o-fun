# agents/betting_agent.py
import logging
import time
import random

from core.agent_registry import register_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

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
        self.bet_threshold = 1.5
        self.simulated_events = ["event1", "event2", "event3"]
        self.bet_interval = 30
        
        # Risk management and simulation parameters
        self.account_balance = 1000.0
        self.total_bets = 0
        self.successful_bets = 0
        self.failed_bets = 0
        self.bet_success_rate = 0.66
        
        # Placeholder for API
        self.api = None

    def run(self):
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
                    self.total_bets += 1
                    self.logger.error(f"[BETTING AGENT] Error processing event {event}: {e}", exc_info=True)
                time.sleep(1)
            self.logger.info("[BETTING AGENT] Completed betting cycle. Sleeping until next cycle...")
            time.sleep(self.bet_interval)

    def fetch_betting_odds(self, event_id):
        simulated_odds = random.uniform(1.0, 3.0)
        self.logger.info(f"[BETTING AGENT] Fetched odds for {event_id}: {simulated_odds:.2f}")
        return simulated_odds

    def analyze_betting_strategy(self, odds):
        if odds > self.bet_threshold:
            amount = round(100 * (odds - self.bet_threshold), 2)
            self.logger.info(f"[BETTING AGENT] Decision: Odds {odds:.2f} exceed threshold {self.bet_threshold}. Calculated bet amount: ${amount}")
            return True, "back", amount
        return False, None, 0

    def place_bet(self, event, bet_type, amount, odds, mock=True):
        try:
            if mock or self.api is None:
                self.logger.info(f"[BETTING AGENT] Mock bet placed: {event}, type={bet_type}, amount={amount}, odds={odds}")
                success = random.random() < self.bet_success_rate
                if success:
                    profit = round(amount * (odds - 1), 2)
                    self.account_balance += profit
                    self.successful_bets += 1
                    self.total_bets += 1
                    return f"Success: {bet_type} bet of ${amount} placed on {event} won (profit: ${profit})."
                else:
                    self.account_balance -= amount
                    self.failed_bets += 1
                    self.total_bets += 1
                    return f"Failed: {bet_type} bet of ${amount} placed on {event} lost."
            else:
                response = self.api.place_bet(event, amount, odds)
                self.logger.info(f"[BETTING AGENT] Bet placed successfully: {event}, type={bet_type}, amount={amount}, odds={odds}")
                if response.get("status") == "success":
                    self.account_balance += response.get("profit", 0)
                    self.successful_bets += 1
                else:
                    self.account_balance -= amount
                    self.failed_bets += 1
                self.total_bets += 1
                return f"Bet placed via API: {response.get('message', 'No message')}"
        except Exception as e:
            self.logger.error(f"[BETTING AGENT] Bet placement failed for {event}: {e}", exc_info=True)
            self.account_balance -= amount
            self.failed_bets += 1
            self.total_bets += 1
            return f"Error: Bet placement failed for {event}. Lost ${amount}."

    def stop(self):
        self.status = "stopped"
        self.logger.info("[BETTING AGENT] Agent stopped.")

    def health_check(self):
        return {
            "status": self.status,
            "uptime": "TODO: add uptime tracking",
            "last_error": None,
            "account_balance": self.account_balance
        }

    def get_metrics(self):
        error_rate = (self.failed_bets / self.total_bets) if self.total_bets > 0 else 0
        return {
            "total_bets": self.total_bets,
            "successful_bets": self.successful_bets,
            "failed_bets": self.failed_bets,
            "error_rate": round(error_rate, 2),
            "current_balance": round(self.account_balance, 2)
        }
