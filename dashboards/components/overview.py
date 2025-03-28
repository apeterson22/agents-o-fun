from dash import html, dcc, Input, Output
import datetime
import random

TAB_ID = "overview"
TAB_LABEL = "Overview"

def render_layout():
    return html.Div([
        html.H2("System Overview"),
        html.Div(id="live-status-panel"),
        dcc.Interval(id="overview-refresh", interval=5000, n_intervals=0)  # 5s auto-refresh
    ])

def register_callbacks(app):
    @app.callback(Output("live-status-panel", "children"), Input("overview-refresh", "n_intervals"))
    def update_health_status(n):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        statuses = {
            "Fidelity API": random.choice(["OK ✅", "Degraded ⚠️", "Offline ❌"]),
            "Crypto API": random.choice(["OK ✅", "Timeout ⚠️", "Offline ❌"]),
            "Betting API": random.choice(["OK ✅", "Error ❌"]),
            "Trading Engine": random.choice(["Running ✅", "Paused ⏸️"]),
            "RL Trainer": random.choice(["Active 🧠", "Idle 😴", "Error ❌"]),
        }
        return html.Ul([html.Li(f"{k}: {v} ({now})") for k, v in statuses.items()])

