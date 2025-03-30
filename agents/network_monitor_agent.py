import sqlite3
import time
import threading
import random
from datetime import datetime
from core.agent_registry import register_agent
from utils.network_utils import scan_network_devices  # You can extract this from the plugin shell
import logging

DB_FILE = "training_data.db"

@register_agent("network-monitoring", description="Monitors network activity and pushes scan metrics", model="custom", data_source="network_traffic.db")
class NetworkMonitoringAgent:
    def __init__(self):
        self.status = "idle"
        self.scan_mode = "scheduled"  # Options: manual, scheduled, idle
        self.scan_interval = 300  # Default 5 minutes
        self.last_scan_time = 0
        self.thread = threading.Thread(target=self.scheduler_loop, daemon=True)
        self.running = True
        self._setup_database()
        self.thread.start()

    def _setup_database(self):
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS network_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    scan_duration REAL,
                    device_count INTEGER,
                    interface TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    component TEXT,
                    level TEXT,
                    message TEXT
                )
            """)
            conn.commit()

    def log(self, level, message):
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO logs (timestamp, component, level, message) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), "network-monitoring", level.upper(), message)
            )

    def scheduler_loop(self):
        while self.running:
            now = time.time()
            if self.scan_mode == "scheduled" and now - self.last_scan_time >= self.scan_interval:
                self.run_scan()
            elif self.scan_mode == "idle" and self.status == "idle":
                self.run_scan()
            time.sleep(5)

    def run_scan(self, trigger="auto"):
        try:
            self.status = "scanning"
            self.last_scan_time = time.time()
            self.log("info", f"Triggered scan ({trigger})")
            start = time.time()

            # Simulate actual device discovery
            devices = scan_network_devices()
            device_count = len(devices)

            duration = time.time() - start

            with sqlite3.connect(DB_FILE) as conn:
                for iface, dev_list in devices.items():
                    conn.execute(
                        "INSERT INTO network_metrics (timestamp, scan_duration, device_count, interface) VALUES (?, ?, ?, ?)",
                        (datetime.now().isoformat(), duration, len(dev_list), iface)
                    )
            self.log("info", f"Completed scan: {device_count} devices in {duration:.2f}s")
        except Exception as e:
            self.log("error", f"Scan failed: {e}")
        finally:
            self.status = "idle"

    def manual_trigger(self):
        self.run_scan(trigger="manual")

    def stop(self):
        self.running = False
        self.thread.join()

