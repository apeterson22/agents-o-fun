import dash
from dash import html, dcc, Input, Output, State
import requests
import pandas as pd
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate

# Configuration for HTTP server (matches network_monitor.sh)
HTTP_URL = "http://0.0.0.0:8081"  # Adjust if server runs elsewhere
HTTP_USER = 'admin'
HTTP_PASS = 'super!secret'  # Match password from network_monitor.sh

TAB_ID = "network-monitoring"
TAB_LABEL = "Network Monitoring"

class NetworkMonitoringTab:
    TAB_ID = "network-monitoring"
    TAB_LABEL = "Network Monitoring"

    def __init__(self):
        self.auth = (HTTP_USER, HTTP_PASS)

    def fetch_data(self, endpoint, interface=None):
        """Fetch data from the network_monitor.sh HTTP server."""
        url = f"{HTTP_URL}{endpoint}"
        if interface:
            url += f"?interface={interface}"
        try:
            response = requests.get(url, auth=self.auth, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching {endpoint}: {e}")
            return []

    def render_layout(self):
        """Define the layout for the network monitoring tab."""
        return html.Div([
            html.H3("Network Traffic Monitoring", className="text-center my-3"),
            # Controls
            html.Div([
                dcc.Dropdown(
                    id="interface-filter",
                    options=[],
                    placeholder="Select Interface",
                    className="form-control w-25 d-inline-block"
                ),
                html.Button("Refresh", id="refresh-btn", className="btn btn-primary ms-2"),
                dcc.Interval(id="auto-refresh", interval=60*1000, n_intervals=0),  # Refresh every 60s
            ], className="mb-3"),
            # Traffic Graph
            dcc.Graph(id="traffic-graph"),
            # Device Table
            html.H4("Discovered Devices", className="mt-4"),
            dcc.Graph(id="device-table"),  # Using Graph for table
        ])

    def register_callbacks(self, app):
        """Register callbacks for interactivity."""

        @app.callback(
            Output("interface-filter", "options"),
            Input("auto-refresh", "n_intervals")
        )
        def update_interface_options(n_intervals):
            devices = self.fetch_data("/devices")
            interfaces = sorted(set(d["interface"] for d in devices if d["interface"]))
            return [{"label": iface, "value": iface} for iface in interfaces]

        @app.callback(
            [Output("traffic-graph", "figure"),
             Output("device-table", "figure")],
            [Input("refresh-btn", "n_clicks"),
             Input("auto-refresh", "n_intervals")],
            [State("interface-filter", "value")]
        )
        def update_dashboard(n_clicks, n_intervals, interface_filter):
            # Fetch traffic data
            traffic_data = self.fetch_data("/traffic", interface_filter)
            if not traffic_data:
                traffic_fig = go.Figure()
                traffic_fig.update_layout(title="No Traffic Data Available")
            else:
                df = pd.DataFrame(traffic_data)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                
                traffic_fig = go.Figure()
                for iface in df["interface"].unique():
                    iface_df = df[df["interface"] == iface]
                    traffic_fig.add_trace(go.Scatter(
                        x=iface_df["timestamp"],
                        y=iface_df["id"].cumcount() + 1,
                        mode="lines",
                        name=f"{iface} Traffic",
                        hovertemplate="Time: %{x}<br>Packets: %{y}"
                    ))
                traffic_fig.update_layout(
                    title="Network Traffic Over Time",
                    xaxis_title="Time",
                    yaxis_title="Cumulative Packets",
                    legend_title="Interface"
                )

            # Fetch device data
            device_data = self.fetch_data("/devices", interface_filter)
            if not device_data:
                device_fig = go.Figure()
                device_fig.update_layout(title="No Devices Detected")
            else:
                df_devices = pd.DataFrame(device_data)
                device_fig = go.Figure(data=[go.Table(
                    header=dict(values=["IP", "Hostname", "MAC", "Interface", "Last Seen"],
                                fill_color="paleturquoise",
                                align="left"),
                    cells=dict(values=[df_devices["ip"], df_devices["hostname"], df_devices["mac"],
                                       df_devices["interface"], df_devices["last_seen"]],
                               fill_color="lavender",
                               align="left"))
                ])
                device_fig.update_layout(title="Network Devices")

            return traffic_fig, device_fig
