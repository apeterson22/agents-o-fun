import threading
import logging

AGENT_REGISTRY = {}
AGENT_STATUS = {}

def register_agent(agent_name, **metadata):
    """
    Decorator to register an agent class.
    """
    def wrapper(cls):
        AGENT_REGISTRY[agent_name] = {
            "class": cls,
            "metadata": metadata,
        }
        AGENT_STATUS[agent_name] = "stopped"
        return cls
    return wrapper

def get_registered_agents():
    """
    Return a dictionary of registered agents with their status, metadata, class, and a placeholder for health.
    """
    result = {}
    for name, info in AGENT_REGISTRY.items():
        result[name] = {
            "status": AGENT_STATUS.get(name, "unknown"),
            "metadata": info.get("metadata", {}),
            "class": info.get("class"),
            "health": None  # To be updated at runtime
        }
    return result

def control_agent(name, action):
    try:
        if name not in AGENT_REGISTRY:
            return f"Agent '{name}' not found."
        action = action.strip().lower()
        if action == "start":
            if AGENT_STATUS.get(name) == "running":
                return f"Agent '{name}' already running."
            AGENT_STATUS[name] = "running"
            return f"Agent '{name}' started."
        elif action == "stop":
            AGENT_STATUS[name] = "stopped"
            return f"Agent '{name}' stopped."
        elif action == "restart":
            AGENT_STATUS[name] = "running"
            return f"Agent '{name}' restarted."
        else:
            return f"Unknown action '{action}'."
    except Exception as e:
        logging.exception(f"Error during {action} of {name}: {e}")
        return f"Error during {action} of {name}"

