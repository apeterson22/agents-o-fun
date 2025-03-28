import json
import logging
from core.agent_registry import register_agent, AGENT_REGISTRY, AGENT_STATUS

# Optional: You can extend this registry to include metadata
AGENT_METADATA = {}

CONFIG_PATH = "configs/agents_config.json"

def load_agents_from_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            agents = config.get("agents", [])

            for agent in agents:
                name = agent.get("name")
                description = agent.get("description", "")
                model_type = agent.get("model_type", "unknown")
                data_source = agent.get("data_source", "")

                # Store metadata
                AGENT_METADATA[name] = {
                    "description": description,
                    "model_type": model_type,
                    "data_source": data_source,
                    "status": "stopped"
                }

                # Dynamically create a stub class and register it
                @register_agent(name)
                class GenericAgent:
                    def run(self):
                        logging.info(f"[{name.upper()} AGENT] Running agent: {description}")
                        logging.info(f"  • Model: {model_type}")
                        logging.info(f"  • Data Source: {data_source}")
                        # Simulate agent behavior
                        print(f"[{name}] Agent started and running...")

                logging.info(f"[AgentLoader] Registered agent '{name}' from config.")

    except Exception as e:
        logging.exception(f"[AgentLoader] Failed to load agents: {e}")

