# dashboards/components/overview.py
from dash import html, dcc, Input, Output
import datetime
import random

TAB_ID = "overview"
TAB_LABEL = "Overview"

class OverviewTab:
    def __init__(self, agent_manager=None):
        self.agent_manager = agent_manager
    TAB_ID = TAB_ID
    TAB_LABEL = TAB_LABEL

    def render_layout(self):
        return html.Div([
            html.H2("System Overview"),
            html.Div(id="live-status-panel"),
            dcc.Interval(id="overview-refresh", interval=5000, n_intervals=0)
        ])

    def register_callbacks(self, app):
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


_tab = OverviewTab()
render_layout = _tab.render_layout
register_callbacks = _tab.register_callbacks

