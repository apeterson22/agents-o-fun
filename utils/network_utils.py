import requests

def scan_network_devices():
    """Simulate pulling data from the network monitor's exposed HTTP API."""
    devices_resp = requests.get("http://127.0.0.1:8082/devices", auth=("admin", "supersecret"), timeout=5)  # Updated URL and password
    devices = devices_resp.json()

    grouped = {}
    for d in devices:
        iface = d.get("interface", "unknown")
        grouped.setdefault(iface, []).append(d)
    return grouped
