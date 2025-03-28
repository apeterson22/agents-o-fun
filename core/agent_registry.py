
import threading
import logging

AGENT_REGISTRY = {}
AGENT_STATUS = {}
AGENT_THREADS = {}

def register_agent(agent_name):
    def wrapper(cls):
        AGENT_REGISTRY[agent_name] = cls
        AGENT_STATUS[agent_name] = "stopped"
        return cls
    return wrapper

def get_registered_agents():
    return {k: {"status": AGENT_STATUS.get(k, "unknown")} for k in AGENT_REGISTRY}

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
        cls = AGENT_REGISTRY[name]
        instance = cls()
        instance.run()
    except Exception as e:
        logging.exception(f"[AgentExecution] Failed to run {name}: {e}")
        AGENT_STATUS[name] = "error"
