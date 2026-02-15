# core/agent_manager.py
import logging
from core.agent_registry import control_agent, get_registered_agents

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

class AgentManager:
    def __init__(self):
        self.agents = get_registered_agents()

    def start_agent(self, agent_id):
        """Start an agent by ID."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent '{agent_id}' not found")
        return control_agent(agent_id, "start")

    def stop_agent(self, agent_id):
        """Stop an agent by ID."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent '{agent_id}' not found")
        return control_agent(agent_id, "stop")

    def get_agent_status(self, agent_id):
        """Get the status of an agent."""
        agent = self.agents.get(agent_id)
        return agent["status"] if agent else "unknown"
