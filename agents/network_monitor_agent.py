# agents/network_monitor_agent.py
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from core.agent_registry import register_agent
from utils.network_utils import scan_network_devices, get_traffic_stats, get_routing_settings, update_routing_settings
from utils.system_utils import get_system_metrics
import logging

log = logging.getLogger(__name__)
DB_FILE = "databases/network_traffic.db"

@register_agent("network-monitoring", description="Monitors network activity and optimizes routing", model="custom", data_source="local_traffic")
class NetworkMonitorAgent:
    def __init__(self):
        self.status = "idle"
        self.scan_mode = "scheduled"
        self.scan_interval = 300  # 5 minutes for device scans
        self.optimization_interval = 60  # 1 minute for optimizations
        self.last_scan_time = 0
        self.last_optimization_time = 0
        self.db_path = DB_FILE
        # Remove parameters that are not used by the utility functions:
        # self.target_ip, self.username, self.password are not passed to get_traffic_stats/get_routing_settings.
        self._setup_database()

    def _setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
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
                CREATE TABLE IF NOT EXISTS traffic_data (
                    timestamp TEXT,
                    device_ip TEXT,
                    interface TEXT,
                    bytes_sent INTEGER,
                    bytes_received INTEGER,
                    latency_ms REAL,
                    packet_loss REAL
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
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    timestamp TEXT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    bytes_sent INTEGER,
                    bytes_recv INTEGER
                )
                """
            )
            conn.commit()

    def log(self, level, message):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO logs (timestamp, component, level, message) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), "network-monitoring", level.upper(), message)
            )

    def scheduler_loop(self):
        # Instead of running continuously, we run only one cycle.
        self.analyze_and_optimize()

    def save_traffic_data(self, traffic_stats):
        with sqlite3.connect(self.db_path) as conn:
            for stat in traffic_stats:
                conn.execute(
                    "INSERT INTO traffic_data (timestamp, device_ip, interface, bytes_sent, bytes_received, latency_ms, packet_loss) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (stat["timestamp"], stat["device_ip"], stat["interface"],
                     stat["bytes_sent"], stat["bytes_received"], stat["latency_ms"], stat["packet_loss"])
                )
        log.info("[NetworkMonitorAgent] Saved traffic data.")

    def analyze_and_optimize(self):
        # Record local system metrics for monitoring
        metrics = get_system_metrics()
        self.save_system_metrics(metrics)

        # Call utility functions without unsupported extra parameters.
        traffic_stats = get_traffic_stats()
        if not traffic_stats:
            return

        self.save_traffic_data(traffic_stats)
        routing_settings = get_routing_settings()
        if not routing_settings:
            return

        now = datetime.now()
        five_min_ago = now - timedelta(minutes=5)
        recent_stats = [stat for stat in traffic_stats if datetime.fromisoformat(stat["timestamp"]) >= five_min_ago]

        if not recent_stats:
            return

        device_usage = {}
        for stat in recent_stats:
            key = (stat["device_ip"], stat["interface"])
            if key not in device_usage:
                device_usage[key] = {"bytes_sent": 0, "bytes_received": 0, "count": 0}
            device_usage[key]["bytes_sent"] += stat["bytes_sent"]
            device_usage[key]["bytes_received"] += stat["bytes_received"]
            device_usage[key]["count"] += 1

        for key in device_usage:
            total_bytes = device_usage[key]["bytes_sent"] + device_usage[key]["bytes_received"]
            total_seconds = device_usage[key]["count"]
            bandwidth_mbps = (total_bytes * 8 / 1e6) / total_seconds
            device_usage[key]["bandwidth_mbps"] = bandwidth_mbps

        for iface in routing_settings["interfaces"]:
            iface_name = iface["name"]
            max_bandwidth = iface["max_bandwidth_mbps"]
            current_usage = sum(usage["bandwidth_mbps"] for (ip, ifc), usage in device_usage.items() if ifc == iface_name)

            if current_usage > 0.8 * max_bandwidth:
                top_users = sorted(
                    [(ip, usage["bandwidth_mbps"]) for (ip, ifc), usage in device_usage.items() if ifc == iface_name],
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                for ip, _ in top_users:
                    current_rules = [rule for rule in iface.get("qos_rules", []) if rule.get("device_ip") == ip]
                    if not current_rules or current_rules[0].get("priority") != "high":
                        iface["qos_rules"] = [rule for rule in iface.get("qos_rules", []) if rule.get("device_ip") != ip]
                        iface.setdefault("qos_rules", []).append({"device_ip": ip, "priority": "high"})
                        self.log("info", f"Set high priority for device {ip} on {iface_name}")

        update_routing_settings(routing_settings)
        self.log("info", "Applied routing optimizations.")

    def save_system_metrics(self, metrics):
        """Persist system metrics to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO system_metrics (timestamp, cpu_percent, memory_percent, disk_percent, bytes_sent, bytes_recv) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now().isoformat(),
                    metrics["cpu_percent"],
                    metrics["memory_percent"],
                    metrics["disk_percent"],
                    metrics["bytes_sent"],
                    metrics["bytes_recv"],
                ),
            )

    def run(self):
        """
        Run the network analysis once.
        (This method will be triggered manually via the dashboard.)
        """
        self.scheduler_loop()
        self.status = "stopped"


