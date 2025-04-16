# core/agent_registry.py
import logging
import threading
from functools import wraps

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

class AgentRegistry:
    _registry = {}
    _instances = {}
    _threads = {}
    _lock = threading.Lock()

    @classmethod
    def register_agent(cls, name, agent_class, description="", model="", data_source=""):
        """
        Register an agent with its metadata.

        Args:
            name (str): Unique agent name.
            agent_class (type): The agent class.
            description (str): Description of the agent.
            model (str): Model type used by the agent.
            data_source (str): Data source for the agent.
        """
        if not name:
            raise ValueError("Agent name is required")
        with cls._lock:
            cls._registry[name] = {
                "status": "stopped",
                "metadata": {
                    "description": description,
                    "model": model,
                    "data_source": data_source
                },
                "class": agent_class,
                "health": None
            }
        logging.info(f"[AgentRegistry] Registered agent '{name}' with class {agent_class.__name__}")

    @classmethod
    def control_agent(cls, name, action):
        """
        Control an agent's lifecycle (start, stop, restart).

        Args:
            name (str): Agent name.
            action (str): Action to perform (start, stop, restart).

        Returns:
            str: Result message.
        """
        with cls._lock:
            if name not in cls._registry:
                return f"Agent '{name}' not found."
            agent_info = cls._registry[name]
            action = action.lower()

        if action == "start":
            with cls._lock:
                if agent_info["status"] == "running":
                    return f"Agent '{name}' already running."
            try:
                if name not in cls._instances:
                    cls._instances[name] = agent_info["class"]()
                thread = threading.Thread(target=cls._run_agent, args=(name,), daemon=True)
                thread.start()
                with cls._lock:
                    cls._threads[name] = thread
                    agent_info["status"] = "running"
                    agent_info["health"] = cls._instances[name].health_check() if hasattr(cls._instances[name], "health_check") else "Running"
                return f"Agent '{name}' started."
            except Exception as e:
                logging.exception(f"[AgentControl] Failed to start {name}: {e}")
                return f"Error starting {name}: {e}"

        elif action == "stop":
            with cls._lock:
                if agent_info["status"] == "stopped":
                    return f"Agent '{name}' already stopped."
                agent_info["status"] = "stopped"
                if name in cls._instances and hasattr(cls._instances[name], "stop"):
                    cls._instances[name].stop()
                agent_info["health"] = cls._instances[name].health_check() if name in cls._instances and hasattr(cls._instances[name], "health_check") else "Stopped"
            return f"Agent '{name}' stopped."

        elif action == "restart":
            cls.control_agent(name, "stop")
            return cls.control_agent(name, "start")

        return f"Unknown action '{action}'."

    @classmethod
    def _run_agent(cls, name):
        try:
            with cls._lock:
                instance = cls._instances[name]
                metadata = cls._registry[name]["metadata"]
            logging.info(f"[{name.upper()} AGENT] Running agent: {metadata.get('description', 'No description')}")
            for k, v in metadata.items():
                logging.info(f"  • {k.capitalize()}: {v}")
            instance.run()
        except Exception as e:
            logging.exception(f"[AgentExecution] Failed to run {name}: {e}")
            with cls._lock:
                cls._registry[name]["status"] = "error"
                cls._registry[name]["health"] = f"Error: {e}"

    @classmethod
    def get_agent(cls, name):
        """Retrieve an agent by name."""
        return cls._registry.get(name)

    @classmethod
    def get_registered_agents(cls):
        """Return all registered agents."""
        with cls._lock:
            return cls._registry

def register_agent(name, description="", model="", data_source=""):
    """
    Register an agent as a decorator or function.

    Args:
        name (str): Unique agent name.
        description (str): Description of the agent.
        model (str): Model type used by the agent.
        data_source (str): Data source for the agent.

    Returns:
        callable: Decorator function if used as decorator, else None.
    """
    def decorator(agent_class):
        @wraps(agent_class)
        def wrapper(*args, **kwargs):
            return agent_class(*args, **kwargs)
        AgentRegistry.register_agent(name, agent_class, description, model, data_source)
        return wrapper
    return decorator

def control_agent(name, action):
    """Convenience function to control an agent."""
    return AgentRegistry.control_agent(name, action)

def get_registered_agents():
    """Convenience function to get all registered agents."""
    return AgentRegistry.get_registered_agents()
