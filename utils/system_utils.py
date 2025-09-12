"""Utility functions for monitoring local system metrics."""
import psutil
import logging
from typing import Dict

logger = logging.getLogger("SystemUtils")


def get_system_metrics() -> Dict[str, float]:
    """Collect basic system metrics.

    Returns:
        Dict[str, float]: CPU, memory, and disk usage percentages along with
        network I/O statistics.
    """
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage('/').percent
    net_io = psutil.net_io_counters()
    metrics = {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "bytes_sent": net_io.bytes_sent,
        "bytes_recv": net_io.bytes_recv,
    }
    logger.debug("Collected system metrics: %s", metrics)
    return metrics
