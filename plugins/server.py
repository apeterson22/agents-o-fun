#!/usr/bin/env python3
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import base64

USER = "admin"
PASS = "supersecret"
DB_FILE = "/apps/Solomon/agents-o-fun/databases/network_traffic.db"

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

httpd = HTTPServer(('0.0.0.0', 8082), Handler)
print(f"Server running on port 8082")
httpd.serve_forever()
