from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import dash
from core.agent_registry import control_agent, get_registered_agents
import logging

# Constants for the tab
TAB_ID = "decision-engine"
TAB_LABEL = "Decision Engine"

class DecisionEngineTab:
    def __init__(self, agent_manager=None):
        self.agent_manager = agent_manager
    TAB_ID = TAB_ID
    TAB_LABEL = TAB_LABEL

    def render_layout(self):
        return html.Div([
            html.H3("Decision Engine Control Panel"),
            html.Div(id="de-status", children="Status: Not running"),
            dbc.Button("Start Decision Engine", id="btn-start-de", color="success", n_clicks=0),
            dbc.Button("Stop Decision Engine", id="btn-stop-de", color="danger", n_clicks=0, style={"marginLeft": "10px"}),
            dbc.Button("Refresh Status", id="btn-refresh-de", color="primary", n_clicks=0, style={"marginLeft": "10px"}),
            html.Div(id="de-metrics", children="Metrics: N/A"),
            dcc.Interval(id="de-interval", interval=10000, n_intervals=0)
        ], className="p-4")

    def register_callbacks(self, app):
        @app.callback(
            Output("de-status", "children"),
            Output("de-metrics", "children"),
            Input("btn-start-de", "n_clicks"),
            Input("btn-stop-de", "n_clicks"),
            Input("btn-refresh-de", "n_clicks"),
            Input("de-interval", "n_intervals")
        )
        def update_de_status(n_start, n_stop, n_refresh, n_intervals):
            ctx = dash.callback_context
            if not ctx.triggered:
                action = "refresh"
            else:
                trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
                if trigger_id == "btn-start-de":
                    action = "start"
                elif trigger_id == "btn-stop-de":
                    action = "stop"
                else:
                    action = "refresh"
            # Control the decision engine agent
            result = control_agent("decision-engine", action)
            # Retrieve health status from the registered agents
            agents = get_registered_agents()
            health = agents.get("decision-engine", {}).get("health", "No metrics available")
            status_text = f"Decision Engine Status: {result}"
            metrics_text = f"Metrics: {health}"
            return status_text, metrics_text

# Expose the tab's layout and callbacks for the dashboard loader
de_tab = DecisionEngineTab()
render_layout = de_tab.render_layout
register_callbacks = de_tab.register_callbacks

