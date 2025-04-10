# core/agent_manager.py
import logging
import threading
from core.agent_registry import get_registered_agents

class AgentManager:
    def __init__(self):
        self.instances = {}
        self.threads = {}
        self.lock = threading.Lock()

    def get_agent_status(self, agent_id):
        with self.lock:
            if agent_id in self.instances:
                thread = self.threads[agent_id]
                return "running" if thread.is_alive() else "stopped"
            return "not started"

    def start_agent(self, agent_id, **kwargs):
        with self.lock:
            agents = get_registered_agents()
            agent_info = agents.get(agent_id)
            if not agent_info:
                raise ValueError(f"Agent '{agent_id}' not registered.")

            agent_class = agent_info["class"]
            try:
                instance = agent_class(**kwargs)
                thread = threading.Thread(target=instance.run, name=agent_id, daemon=True)
                self.instances[agent_id] = instance
                self.threads[agent_id] = thread
                thread.start()
                logging.info(f"Agent {agent_id} started.")
                return f"Agent {agent_id} started."
            except Exception as e:
                logging.error(f"Failed to start agent {agent_id}: {e}")
                return f"Failed to start agent {agent_id}: {e}"

    def stop_agent(self, agent_id):
        with self.lock:
            if agent_id in self.instances:
                agent = self.instances[agent_id]
                if hasattr(agent, "stop"):
                    try:
                        agent.stop()
                    except Exception as e:
                        logging.error(f"Error stopping agent {agent_id}: {e}")
                thread = self.threads[agent_id]
                thread.join(timeout=5)
                del self.instances[agent_id]
                del self.threads[agent_id]
                logging.info(f"Agent {agent_id} stopped.")
                return f"Agent {agent_id} stopped."
            return f"Agent {agent_id} not found."

    def restart_agent(self, agent_id, **kwargs):
        self.stop_agent(agent_id)
        return self.start_agent(agent_id, **kwargs)

    def get_status(self):
        with self.lock:
            return {
                aid: {
                    "alive": thread.is_alive(),
                    "class": instance.__class__.__name__,
                }
                for aid, (instance, thread) in zip(self.instances.keys(), zip(self.instances.values(), self.threads.values()))
            }

