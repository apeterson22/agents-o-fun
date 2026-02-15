import os

agent_specs = [
    {
        "filename": "crypto_agent.py",
        "classname": "CryptoAgent",
        "agent_name": "crypto",
        "description": "Crypto market analysis agent",
        "model": "LLM",
        "data_source": "exchange_data, social_media"
    },
    {
        "filename": "betting_agent.py",
        "classname": "BettingAgent",
        "agent_name": "betting",
        "description": "Sports and betting odds analysis",
        "model": "LLM",
        "data_source": "betting_lines, sports_feeds"
    },
    {
        "filename": "ml_predictor.py",
        "classname": "MLPredictorAgent",
        "agent_name": "ml-predictor",
        "description": "ML-driven forecasting for trends",
        "model": "MLModel",
        "data_source": "historical_data, csv_uploads"
    },
    {
        "filename": "marketing_agent.py",
        "classname": "MarketingGuru",
        "agent_name": "marketing-guru",
        "description": "AI agent for marketing strategy",
        "model": "LLM",
        "data_source": "social_media, trend_data"
    }
]

template = '''from core.agent_registry import register_agent
import logging

@register_agent("{agent_name}", description="{description}", model="{model}", data_source="{data_source}")
class {classname}:
    def __init__(self):
        self.status = "initialized"
        self.logger = logging.getLogger("{agent_name}")
        self.metadata = {{
            "description": "{description}",
            "model": "{model}",
            "data_source": "{data_source}"
        }}

    def start(self):
        self.status = "running"
        self.logger.info("[{agent_name_upper} AGENT] Running agent: {description}")
        self.logger.info("  • Model: {model}")
        self.logger.info("  • Data Source: {data_source}")

    def stop(self):
        self.status = "stopped"
        self.logger.info("[{agent_name_upper} AGENT] Agent stopped.")

    def health_check(self):
        return {{
            "status": self.status,
            "uptime": "TODO: add uptime tracking",
            "last_error": None
        }}

    def get_metrics(self):
        return {{
            "custom_stat_1": 0,
            "custom_stat_2": 0,
            "error_rate": 0.0
        }}
'''

# Adjust this path if running elsewhere
base_path = "agents"
os.makedirs(base_path, exist_ok=True)

for spec in agent_specs:
    spec["agent_name_upper"] = spec["agent_name"].upper()
    with open(os.path.join(base_path, spec["filename"]), "w") as f:
        f.write(template.format(**spec))

