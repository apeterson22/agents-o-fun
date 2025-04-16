# dashboards/components/admin.py
import logging
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
from core.agent_registry import get_registered_agents, control_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

class AdminTab:
    TAB_ID = "admin"
    TAB_LABEL = "Admin"

    def __init__(self, agent_manager=None):
        self.agent_manager = agent_manager

    def render_layout(self):
        agents = get_registered_agents()
        if not agents:
            return html.Div("No agents registered", className="alert alert-warning")
        
        if len(agents) <= 6:
            layout = [
                html.H3("Agent Control", className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        html.H5(f"Agent: {name}", className="mt-2"),
                        html.P(f"Status: {meta['status']}", id=f"status-{name}", className="text-muted"),
                        dcc.Dropdown(
                            id=f"action-{name}",
                            options=[
                                {"label": "Start", "value": "start"},
                                {"label": "Stop", "value": "stop"},
                                {"label": "Restart", "value": "restart"},
                            ],
                            placeholder="Select action",
                            className="mb-2"
                        ),
                        dbc.Button("Execute", id=f"btn-{name}", color="primary", n_clicks=0)
                    ], width=4, className="mb-4")
                    for name, meta in agents.items()
                ])
            ]
        else:
            layout = [
                html.H3("Agent Control Panel", className="mb-4"),
                dbc.Row([
                    dbc.Col([
                        dcc.Dropdown(
                            id="multi-agent-dropdown",
                            options=[{"label": k, "value": k} for k in agents],
                            placeholder="Select an agent",
                            className="mb-2"
                        ),
                        html.Div(id="multi-agent-status", className="text-muted mb-2"),
                        dcc.Dropdown(
                            id="multi-action-dropdown",
                            options=[
                                {"label": "Start", "value": "start"},
                                {"label": "Stop", "value": "stop"},
                                {"label": "Restart", "value": "restart"},
                            ],
                            placeholder="Select action",
                            className="mb-2"
                        ),
                        dbc.Button("Execute", id="multi-agent-btn", color="primary", n_clicks=0)
                    ], width=6)
                ])
            ]
        return html.Div(layout, className="p-3")

    def register_callbacks(self, app):
        @app.callback(
            Output("multi-agent-status", "children"),
            Input("multi-agent-btn", "n_clicks"),
            State("multi-agent-dropdown", "value"),
            State("multi-action-dropdown", "value"),
            prevent_initial_call=True
        )
        def handle_multi(n, agent_name, action):
            if not agent_name or not action:
                return html.Div("Select agent and action", className="alert alert-warning")
            result = control_agent(agent_name, action)
            logging.info(f"[AdminPanel] {agent_name}: {result}")
            return html.Div(f"{agent_name}: {result}", className="alert alert-info")

        for agent_name in get_registered_agents():
            @app.callback(
                Output(f"status-{agent_name}", "children"),
                Input(f"btn-{agent_name}", "n_clicks"),
                State(f"action-{agent_name}", "value"),
                prevent_initial_call=True
            )
            def callback(n_clicks, selected_action):
                if not selected_action:
                    return html.Span("Status: No action selected", className="text-warning")
                result = control_agent(agent_name, selected_action)
                logging.info(f"[AdminPanel] {agent_name}: {selected_action} -> {result}")
                return html.Span(f"Status: {result}", className="text-success")
