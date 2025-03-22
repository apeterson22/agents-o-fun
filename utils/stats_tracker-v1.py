import threading


class SharedStatsTracker:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.stats = {
            'latest_reward': 0.0,
            'episode_reward': 0.0,
            'portfolio_value': 10000.0,
            'cash': 10000.0,
            'holdings': 0,
            'price': 0.0,
            'step': 0,
            'episode': 0,
        }
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = SharedStatsTracker()
        return cls._instance

    def update(self, key, value):
        with self._lock:
            self.stats[key] = value

    def update_many(self, data: dict):
        with self._lock:
            for key, value in data.items():
                self.stats[key] = value

    def get(self, key):
        with self._lock:
            return self.stats.get(key, None)

    def get_all(self):
        with self._lock:
            return dict(self.stats)

