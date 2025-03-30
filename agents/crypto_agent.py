# agents/crypto_agent.py

from core.agent_registry import register_agent
import logging
import time

@register_agent("crypto", description="Crypto market analysis agent", model="LLM", data_source="exchange_data, social_media")
class CryptoAgent:
    def __init__(self):
        self.status = "initialized"
        self.logger = logging.getLogger("crypto")
        self.metadata = {
            "description": "Crypto market analysis agent",
            "model": "LLM",
            "data_source": "exchange_data, social_media"
        }

    def run(self):
        self.status = "running"
        self.logger.info("[CRYPTO AGENT] Running agent: Crypto market analysis agent")
        self.logger.info("  • Model: LLM")
        self.logger.info("  • Data Source: exchange_data, social_media")
        while self.status == "running":
            self.logger.info("[CRYPTO AGENT] Scanning markets and social sentiment...")
            time.sleep(10)

    def stop(self):
        self.status = "stopped"
        self.logger.info("[CRYPTO AGENT] Agent stopped.")

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

