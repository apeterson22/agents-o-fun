from core.agent_registry import register_agent
import logging

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

    def start(self):
        self.status = "running"
        self.logger.info("[BETTING AGENT] Running agent: Sports and betting odds analysis")
        self.logger.info("  • Model: LLM")
        self.logger.info("  • Data Source: betting_lines, sports_feeds")

    def stop(self):
        self.status = "stopped"
        self.logger.info("[BETTING AGENT] Agent stopped.")

    def health_check(self):
        return {
            "status": self.status,
            "uptime": "TODO: add uptime tracking",
            "last_error": None
        }

    def get_metrics(self):
        return {
            "custom_stat_1": 0,
            "custom_stat_2": 0,
            "error_rate": 0.0
        }
