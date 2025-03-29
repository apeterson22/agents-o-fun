import logging
import yaml
from core.agent_factory import agent_factory
from core.agent_registry import register_agent

def load_agents_from_config(config_path="configs/agent_config.yaml"):
    try:
        with open(config_path, "r") as f:
            agent_configs = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"[AgentLoader] Failed to load config: {e}")
        return

    for agent_name, agent_data in agent_configs.items():
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

