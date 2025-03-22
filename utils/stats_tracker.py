# Patch SharedStatsTracker to include thread-safe stat storage and retrieval
import threading

class SharedStatsTracker:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._latest_stats = {}
        self._raw_stats = []
        self._data_lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = SharedStatsTracker()
            return cls._instance

    def update_stats(self, latest, raw):
        with self._data_lock:
            self._latest_stats = latest
            self._raw_stats.append(raw)
            if len(self._raw_stats) > 500:
                self._raw_stats.pop(0)

    def get_latest(self):
        with self._data_lock:
            return self._latest_stats

    def get_raw(self):
        with self._data_lock:
            return self._raw_stats.copy()

