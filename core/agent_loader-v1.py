# core/agent_loader.py
import logging
import yaml
import json
import os
from core.agent_factory import agent_factory
from core.agent_registry import register_agent

def load_agents_from_config(config_path="configs/agents_config.yaml"):
    """
    Load agent configurations from a file.
    Supports YAML or JSON based on the file extension.
    Expected structure (for YAML or JSON):
    
    agents:
      trading:
        description: "Fetches and stores stock market data"
        model: "Finance RL Model"
        data_source: "Yahoo Finance"
      crypto:
        description: "Crypto market analysis agent"
        model: "LLM"
        data_source: "exchange_data, social_media"
      ...
    """
    agent_configs = None
    try:
        ext = os.path.splitext(config_path)[1].lower()
        with open(config_path, "r") as f:
            if ext == ".json":
                agent_configs = json.load(f)
            else:
                agent_configs = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"[AgentLoader] Failed to load config: {e}")
        return

    for agent_name, agent_data in agent_configs.get("agents", {}).items():
        try:
            agent_class = agent_factory(agent_name)
            register_agent(
                name=agent_name,
                agent_class=agent_class,
                description=agent_data.get("description", ""),
                model=agent_data.get("model", ""),
                data_source=agent_data.get("data_source", "")
            )
            logging.info(f"[AgentLoader] Registered agent '{agent_name}' from config.")
        except Exception as e:
            logging.exception(f"[AgentLoader] Error registering agent '{agent_name}': {e}")

