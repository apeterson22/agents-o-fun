import dash
from dash import html, dcc, Input, Output, State
import requests
import pandas as pd
import plotly.graph_objs as go
from dash.exceptions import PreventUpdate

HTTP_URL = "http://127.0.0.1:8082"
HTTP_USER = 'admin'
HTTP_PASS = 'supersecret'

TAB_ID = "network-monitoring"
TAB_LABEL = "Network Monitoring"

class NetworkMonitoringTab:
    def __init__(self):
        self.auth = (HTTP_USER, HTTP_PASS)

    def fetch_data(self, endpoint, interface=None):
        url = f"{HTTP_URL}{endpoint}"
        if interface:
            url += f"?interface={interface}"
        try:
            response = requests.get(url, auth=self.auth, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[NetworkMonitoring] Error: {e}")
            return []

    def render_layout(self):
        return html.Div([
            html.H3("Network Traffic Monitoring"),
            html.Div([
                dcc.Dropdown(id="interface-filter", options=[], placeholder="Select Interface"),
                html.Button("Refresh", id="refresh-btn", className="btn btn-primary ms-2"),
                dcc.Interval(id="auto-refresh", interval=60000, n_intervals=0),
            ], className="mb-3"),
            dcc.Graph(id="traffic-graph"),
            html.H4("Discovered Devices"),
            dcc.Graph(id="device-table"),
        ], className="p-4")

    def register_callbacks(self, app):
        @app.callback(
            Output("interface-filter", "options"),
            Input("auto-refresh", "n_intervals")
        )
        def update_interface_options(n):
            devices = self.fetch_data("/devices")
            interfaces = sorted(set(d.get("interface") for d in devices if d.get("interface")))
            return [{"label": i, "value": i} for i in interfaces]

        @app.callback(
            [Output("traffic-graph", "figure"), Output("device-table", "figure")],
            [Input("refresh-btn", "n_clicks"), Input("auto-refresh", "n_intervals")],
            State("interface-filter", "value")
        )
        def update_dashboard(n_clicks, n_intervals, interface_filter):
            traffic_data = self.fetch_data("/traffic", interface_filter)
            traffic_fig = go.Figure()
            if traffic_data:
                df = pd.DataFrame(traffic_data)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                for iface in df["interface"].unique():
                    sub_df = df[df["interface"] == iface]
                    traffic_fig.add_trace(go.Scatter(
                        x=sub_df["timestamp"],
                        y=sub_df["id"].cumcount() + 1,
                        mode="lines",
                        name=f"{iface} Traffic"
                    ))
                traffic_fig.update_layout(title="Traffic", xaxis_title="Time", yaxis_title="Packets")

            device_data = self.fetch_data("/devices", interface_filter)
            device_fig = go.Figure()
            if device_data:
                df_devices = pd.DataFrame(device_data)
                device_fig.add_trace(go.Table(
                    header=dict(values=list(df_devices.columns), fill_color="lightblue", align="left"),
                    cells=dict(values=[df_devices[col] for col in df_devices.columns], fill_color="white", align="left")
                ))
                device_fig.update_layout(title="Discovered Devices")
            return traffic_fig, device_fig

_tab = NetworkMonitoringTab()
render_layout = _tab.render_layout  # no parentheses!
register_callbacks = _tab.register_callbacks

