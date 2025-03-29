#!/bin/bash

# Determine base directory (one level up from plugins/ where the script resides)
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Configuration (relative to BASE_DIR)
CONFIG_FILE="${CONFIG_FILE:-$BASE_DIR/configs/network_monitor.conf}"
DB_FILE="${DB_FILE:-$BASE_DIR/databases/network_traffic.db}"
LOG_FILE="${LOG_FILE:-$BASE_DIR/logs/network_monitor.log}"
CAPTURE_DIR="${CAPTURE_DIR:-$BASE_DIR/captures}"
NETWORK_RANGE="${NETWORK_RANGE:-192.168.1.0/24}"  # Default range, override as needed
HTTP_PORT="${HTTP_PORT:-8081}"
HTTP_USER="${HTTP_USER:-admin}"
HTTP_PASS="${HTTP_PASS:-secret}"  # Change to a secure password

# Load config file if it exists
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Loaded config from $CONFIG_FILE" >> "$LOG_FILE"
fi

# Ensure dependencies are installed
check_deps() {
    local deps=("tcpdump" "nmap" "sqlite3" "python3")
    for dep in "${deps[@]}"; do
        command -v "$dep" >/dev/null 2>&1 || { echo "$dep required. Install with: sudo apt-get install $dep"; exit 1; }
    done
}

# Setup directories and logging
setup_dirs() {
    mkdir -p "$CAPTURE_DIR" "$BASE_DIR/logs" "$BASE_DIR/databases" "$BASE_DIR/configs"
    touch "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Network monitor starting" >> "$LOG_FILE"
}

# Auto-discover network interfaces
discover_interfaces() {
    INTERFACES=($(ip link show | grep -E '^[0-9]+:' | awk -F: '{print $2}' | tr -d ' ' | grep -v 'lo'))
    if [ ${#INTERFACES[@]} -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] No network interfaces found" >> "$LOG_FILE"
        exit 1
    fi
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Discovered interfaces: ${INTERFACES[*]}" >> "$LOG_FILE"
}

# Initialize SQLite database with interface column
setup_database() {
    sqlite3 "$DB_FILE" <<EOF
CREATE TABLE IF NOT EXISTS traffic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    interface TEXT,
    src_ip TEXT,
    dst_ip TEXT,
    protocol TEXT,
    payload INTEGER,
    encrypted INTEGER
);
CREATE TABLE IF NOT EXISTS devices (
    ip TEXT PRIMARY KEY,
    hostname TEXT,
    mac TEXT,
    interface TEXT,
    last_seen TEXT
);
EOF
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Database initialized: $DB_FILE" >> "$LOG_FILE"
}

# Autodiscover network devices with nmap for each interface
autodiscover_network() {
    for iface in "${INTERFACES[@]}"; do
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Autodiscovering devices on $iface ($NETWORK_RANGE)" >> "$LOG_FILE"
        nmap -e "$iface" -sn "$NETWORK_RANGE" -oG - 2>/dev/null | grep "Host:" | while read -r line; do
            ip=$(echo "$line" | awk '{print $2}')
            hostname=$(echo "$line" | awk '{print $3}' | tr -d '()')
            mac=$(nmap -e "$iface" -sP "$ip" | grep -i "MAC Address" | awk '{print $3}' || echo "Unknown")
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            sqlite3 "$DB_FILE" "INSERT OR REPLACE INTO devices (ip, hostname, mac, interface, last_seen) VALUES ('$ip', '$hostname', '$mac', '$iface', '$timestamp');"
        done
    done
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Network autodiscovery completed" >> "$LOG_FILE"
}

# Capture and analyze traffic for all interfaces
capture_traffic() {
    for iface in "${INTERFACES[@]}"; do
        OUTPUT_FILE="$CAPTURE_DIR/traffic_${iface}_$(date +%Y%m%d_%H%M%S).pcap"
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Capturing traffic on $iface to $OUTPUT_FILE" >> "$LOG_FILE"
        
        # Capture packets in background, lightweight options
        tcpdump -i "$iface" -n -c 1000 -w "$OUTPUT_FILE" 2>/dev/null &
        TCPDUMP_PID=$!
        sleep 60  # Capture for 60 seconds
        kill "$TCPDUMP_PID" 2>/dev/null
        wait "$TCPDUMP_PID" 2>/dev/null

        # Analyze captured packets
        tcpdump -r "$OUTPUT_FILE" -n 2>/dev/null | while read -r line; do
            timestamp=$(date '+%Y-%m-%d %H:%M:%S')
            src_ip=$(echo "$line" | awk '{print $3}' | cut -d'.' -f1-4)
            dst_ip=$(echo "$line" | awk '{print $5}' | cut -d'.' -f1-4)
            protocol=$(echo "$line" | awk '{print $2}' | cut -d'.' -f1)
            
            payload=0
            if echo "$line" | grep -q "length [1-9]"; then
                payload=1
            fi
            
            encrypted=0
            if echo "$line" | grep -q ":443"; then
                encrypted=1
            fi

            if [ -n "$src_ip" ] && [ -n "$dst_ip" ]; then
                sqlite3 "$DB_FILE" "INSERT INTO traffic (timestamp, interface, src_ip, dst_ip, protocol, payload, encrypted) VALUES ('$timestamp', '$iface', '$src_ip', '$dst_ip', '$protocol', $payload, $encrypted);"
            fi
        done
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Traffic analysis completed for $iface" >> "$LOG_FILE"
    done
}

# Expose data via a lightweight HTTP server with interface filtering
expose_data() {
    cat <<EOF > "$BASE_DIR/plugins/server.py"
#!/usr/bin/env python3
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64

USER = "$HTTP_USER"
PASS = "$HTTP_PASS"
DB_FILE = "$DB_FILE"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header or auth_header != f'Basic {base64.b64encode(f"{USER}:{PASS}".encode()).decode()}':
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Restricted"')
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        path_parts = self.path.split('?')
        endpoint = path_parts[0]
        params = dict(q.split('=') for q in path_parts[1].split('&')) if len(path_parts) > 1 else {}

        interface_filter = params.get('interface', None)

        if endpoint == '/traffic':
            query = 'SELECT * FROM traffic'
            if interface_filter:
                query += f" WHERE interface = '{interface_filter}'"
            query += ' ORDER BY timestamp DESC LIMIT 1000'
            cursor.execute(query)
            data = [{'id': r[0], 'timestamp': r[1], 'interface': r[2], 'src_ip': r[3], 'dst_ip': r[4], 'protocol': r[5], 'payload': r[6], 'encrypted': r[7]} for r in cursor.fetchall()]
        elif endpoint == '/devices':
            query = 'SELECT * FROM devices'
            if interface_filter:
                query += f" WHERE interface = '{interface_filter}'"
            cursor.execute(query)
            data = [{'ip': r[0], 'hostname': r[1], 'mac': r[2], 'interface': r[3], 'last_seen': r[4]} for r in cursor.fetchall()]
        else:
            data = {'error': 'Invalid endpoint. Use /traffic or /devices'}

        self.wfile.write(json.dumps(data).encode())
        conn.close()

httpd = HTTPServer(('0.0.0.0', $HTTP_PORT), Handler)
print(f"Server running on port $HTTP_PORT")
httpd.serve_forever()
EOF

    chmod +x "$BASE_DIR/plugins/server.py"
    python3 "$BASE_DIR/plugins/server.py" &
    SERVER_PID=$!
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] HTTP server started on port $HTTP_PORT (PID: $SERVER_PID)" >> "$LOG_FILE"
}

# Cleanup function
cleanup() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Shutting down..." >> "$LOG_FILE"
    kill "$SERVER_PID" 2>/dev/null
    exit 0
}

# Trap SIGINT/SIGTERM for graceful shutdown
trap cleanup SIGINT SIGTERM

# Main execution
check_deps
setup_dirs
discover_interfaces
setup_database
autodiscover_network
expose_data

# Dynamic main loop
while true; do
    capture_traffic
    autodiscover_network  # Periodic rediscovery
    sleep 60  # Configurable interval
done
