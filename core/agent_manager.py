# core/agent_manager.py

import threading
from core.agent_registry import get_registered_agents

class AgentManager:
    def __init__(self):
        self.instances = {}
        self.threads = {}

    def start_agent(self, agent_id, **kwargs):
        agents = get_registered_agents()
        agent_class = agents.get(agent_id)
        if not agent_class:
            raise ValueError(f"Agent '{agent_id}' not registered.")
        
        instance = agent_class(**kwargs)
        thread = threading.Thread(target=instance.run, name=agent_id, daemon=True)
        self.instances[agent_id] = instance
        self.threads[agent_id] = thread
        thread.start()
        return f"Agent {agent_id} started."

    def stop_agent(self, agent_id):
        if agent_id in self.instances:
            agent = self.instances[agent_id]
            if hasattr(agent, "stop"):
                agent.stop()
            thread = self.threads[agent_id]
            thread.join(timeout=5)
            del self.instances[agent_id]
            del self.threads[agent_id]
            return f"Agent {agent_id} stopped."
        return f"Agent {agent_id} not found."

    def restart_agent(self, agent_id, **kwargs):
        self.stop_agent(agent_id)
        return self.start_agent(agent_id, **kwargs)

    def get_status(self):
        return {
            aid: {
                "alive": thread.is_alive(),
                "class": instance.__class__.__name__,
            }
            for aid, (instance, thread) in zip(self.instances.keys(), zip(self.instances.values(), self.threads.values()))
        }

