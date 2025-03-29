import threading
import logging

AGENT_REGISTRY = {}
AGENT_STATUS = {}
AGENT_THREADS = {}

def register_agent(agent_name, **metadata):
    """
    Decorator to register an agent class with optional metadata.
    """
    def wrapper(cls):
        AGENT_REGISTRY[agent_name] = {
            "class": cls,
            "metadata": metadata or {},
        }
        AGENT_STATUS[agent_name] = "stopped"
        return cls
    return wrapper

def get_registered_agents():
    """
    Returns registered agents along with status and metadata.
    """
    return {
        name: {
            "status": AGENT_STATUS.get(name, "unknown"),
            "metadata": AGENT_REGISTRY[name].get("metadata", {}),
        }
        for name in AGENT_REGISTRY
    }

def control_agent(name, action):
    try:
        if name not in AGENT_REGISTRY:
            return f"Agent '{name}' not found."

        action = action.strip().lower()

        if action == "start":
            if AGENT_STATUS.get(name) == "running":
                return f"Agent '{name}' already running."
            thread = threading.Thread(target=_run_agent, args=(name,), daemon=True)
            thread.start()
            AGENT_THREADS[name] = thread
            AGENT_STATUS[name] = "running"
            return f"Agent '{name}' started."

        elif action == "stop":
            AGENT_STATUS[name] = "stopped"
            return f"Agent '{name}' marked as stopped (manual stop required)."

        elif action == "restart":
            AGENT_STATUS[name] = "stopped"
            return control_agent(name, "start")

        else:
            return f"Unknown action '{action}'."
    except Exception as e:
        logging.exception(f"[AgentControl] Failed to {action} {name}: {e}")
        return f"Error during {action} of {name}"

def _run_agent(name):
    try:
        cls = AGENT_REGISTRY[name]["class"]
        metadata = AGENT_REGISTRY[name].get("metadata", {})
        instance = cls()
        if hasattr(instance, "run"):
            logging.info(f"[{name.upper()} AGENT] Running agent: {metadata.get('description', 'No description')}")
            if metadata:
                for k, v in metadata.items():
                    logging.info(f"  • {k.capitalize()}: {v}")
            instance.run()
        else:
            logging.warning(f"[AgentExecution] Agent '{name}' has no 'run' method.")
    except Exception as e:
        logging.exception(f"[AgentExecution] Failed to run {name}: {e}")
        AGENT_STATUS[name] = "error"

