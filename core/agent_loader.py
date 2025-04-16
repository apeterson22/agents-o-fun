# core/agent_loader.py
import logging
import yaml
import json
import os
from core.agent_factory import agent_factory
from core.agent_registry import register_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

def load_agents_from_config(config_path="configs/agents_config.yaml"):
    """
    Load agent configurations from a file.
    Supports YAML or JSON based on the file extension.

    Expected structure (for YAML):
        agents:
          trading:
            description: "Fetches and stores stock market data"
            model: "Finance RL Model"
            data_source: "Yahoo Finance"
    Expected structure (for JSON):
        agents:
          - name: trading
            description: "Main trading agent for equities and ETFs"
            model: "RL"
            data_source: "fidelity, simulated_env"
    """
    agent_configs = None
    try:
        ext = os.path.splitext(config_path)[1].lower()
        with open(config_path, "r") as f:
            if ext == ".json":
                data = json.load(f)
                agent_configs = {"agents": {item["name"]: item for item in data.get("agents", [])}}
            else:
                agent_configs = yaml.safe_load(f)
        logging.info(f"[AgentLoader] Loaded config from {config_path}")
    except Exception as e:
        logging.error(f"[AgentLoader] Failed to load config from {config_path}: {e}")
        return

    if not agent_configs or "agents" not in agent_configs:
        logging.error("[AgentLoader] No agents found in config")
        return

    for agent_name, agent_data in agent_configs.get("agents", {}).items():
        try:
            agent_class = agent_factory(agent_name)
            # Register using function call (not decorator)
            register_agent(
                name=agent_name,
                description=agent_data.get("description", ""),
                model=agent_data.get("model", ""),
                data_source=agent_data.get("data_source", "")
            )(agent_class)
            logging.info(f"[AgentLoader] Registered agent '{agent_name}' from config")
        except Exception as e:
            logging.exception(f"[AgentLoader] Error registering agent '{agent_name}': {e}")
