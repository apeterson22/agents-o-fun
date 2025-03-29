# dashboards/state.py

from collections import defaultdict
import threading

# Global shared state for dashboard to store agent stats and health
dashboard_state = {
    "agent_stats": defaultdict(dict),   # e.g., { "trading": {"reward": 123, "loss": 0.2}, ... }
    "agent_health": defaultdict(str),   # e.g., { "trading": "healthy", "crypto": "error" }
    "lock": threading.Lock()            # For thread-safe updates
}

