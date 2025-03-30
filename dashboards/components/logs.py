from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import os

TAB_ID = "logs"
TAB_LABEL = "Logs Viewer"

LOG_DIR = "logs"

def render_layout():
    files = [f for f in os.listdir(LOG_DIR) if f.endswith(".log")]
    return html.Div([
        html.H3("Log Viewer"),
        html.Label("Select Log File"),
        dcc.Dropdown(
            id="logfile-selector",
            options=[{"label": f, "value": f} for f in files],
            value=files[0] if files else None,
            clearable=False
        ),
        dcc.Interval(id="log-refresh", interval=3000, n_intervals=0),
        html.Pre(id="log-output", style={"backgroundColor": "#f4f4f4", "padding": "10px", "height": "500px", "overflowY": "scroll"})
    ], className="p-4")

def register_callbacks(app):
    @app.callback(
        Output("log-output", "children"),
        [Input("log-refresh", "n_intervals"), Input("logfile-selector", "value")]
    )
    def update_logs(n, selected_file):
        if not selected_file:
            return "No log file selected."
        path = os.path.join(LOG_DIR, selected_file)
        try:
            with open(path, "r") as f:
                return f.read()[-10000:]  # Tail last 10k characters
        except Exception as e:
            return f"Error reading log file: {e}"

