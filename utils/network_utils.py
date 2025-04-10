import requests
import logging

# Setup logging for network utilities.
logger = logging.getLogger("NetworkUtils")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Router connection details
HTTP_URL = "http://192.168.0.1:8082"
HTTP_USER = "admin"
HTTP_PASS = "I4mAw35ome!!"

def scan_network_devices():
    """
    Fetch and group devices from the router's network monitor API.
    
    Returns:
        dict: Devices grouped by interface.
    """
    try:
        response = requests.get(f"{HTTP_URL}/devices", auth=(HTTP_USER, HTTP_PASS), timeout=5)
        response.raise_for_status()
        devices = response.json()
        grouped = {}
        for d in devices:
            iface = d.get("interface", "unknown")
            grouped.setdefault(iface, []).append(d)
        logger.info("Scanned %d devices across %d interfaces.", len(devices), len(grouped))
        return grouped
    except requests.RequestException as e:
        logger.error("Error fetching network devices: %s", e)
        return {}

def get_traffic_stats(interface=None):
    """
    Fetch detailed traffic statistics from the router's API.
    
    Parameters:
        interface (str, optional): Specify an interface to filter traffic data.
        
    Returns:
        list: Traffic statistics as a JSON-decoded list.
    """
    url = f"{HTTP_URL}/traffic-stats"
    if interface:
        url += f"?interface={interface}"
    try:
        response = requests.get(url, auth=(HTTP_USER, HTTP_PASS), timeout=5)
        response.raise_for_status()
        stats = response.json()
        logger.info("Fetched traffic stats for interface: %s", interface if interface else "all")
        return stats
    except requests.RequestException as e:
        logger.error("Error fetching traffic stats: %s", e)
        return []

def get_routing_settings():
    """
    Retrieve current routing settings from the router.
    
    Returns:
        dict or None: Routing settings as a JSON-decoded dictionary, or None on error.
    """
    url = f"{HTTP_URL}/routing-settings"
    try:
        response = requests.get(url, auth=(HTTP_USER, HTTP_PASS), timeout=5)
        response.raise_for_status()
        settings = response.json()
        logger.info("Fetched routing settings.")
        return settings
    except requests.RequestException as e:
        logger.error("Error fetching routing settings: %s", e)
        return None

def update_routing_settings(settings):
    """
    Update routing settings on the router.
    
    Parameters:
        settings (dict): New routing settings to apply.
        
    Returns:
        dict or None: Response from the router as JSON, or None on error.
    """
    url = f"{HTTP_URL}/routing-settings"
    try:
        response = requests.post(url, json=settings, auth=(HTTP_USER, HTTP_PASS), timeout=5)
        response.raise_for_status()
        result = response.json()
        logger.info("Updated routing settings successfully.")
        return result
    except requests.RequestException as e:
        logger.error("Error updating routing settings: %s", e)
        return None

