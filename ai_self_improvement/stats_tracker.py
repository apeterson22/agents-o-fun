import threading

class StatsTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.latest_step_stats = {}
        self.episode_stats = []

    def update_step_stats(self, stats: dict):
        with self.lock:
            self.latest_step_stats = stats.copy()

    def record_episode(self, stats: dict):
        with self.lock:
            self.episode_stats.append(stats.copy())
            # Optionally keep only recent N episodes
            self.episode_stats = self.episode_stats[-100:]

    def get_latest_step_stats(self) -> dict:
        with self.lock:
            return self.latest_step_stats.copy()

    def get_episode_stats(self) -> list:
        with self.lock:
            return self.episode_stats.copy()

    def reset(self):
        with self.lock:
            self.latest_step_stats.clear()
            self.episode_stats.clear()

# Global instance for system-wide access
shared_stats_tracker = StatsTracker()

