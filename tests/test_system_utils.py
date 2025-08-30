from utils.system_utils import get_system_metrics


def test_get_system_metrics_returns_values():
    metrics = get_system_metrics()
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_percent" in metrics
    assert "bytes_sent" in metrics
    assert "bytes_recv" in metrics
