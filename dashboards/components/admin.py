
from dash import html, dcc, Input, Output, State, callback_context
from core.agent_registry import get_registered_agents, control_agent
import logging
import json

TAB_ID = "admin"
TAB_LABEL = "Admin"

def render_layout():
    agents = get_registered_agents()
    agent_count = len(agents)

    if agent_count == 0:
        return html.Div("No registered agents found.")

    layout = []
    if agent_count <= 6:
        for name, meta in agents.items():
            layout.append(html.Div([
                html.H5(f"Agent: {name}"),
                html.P(f"Status: {meta['status']}", id=f"status-{name}"),
                dcc.Dropdown(
                    id=f"action-{name}",
                    options=[
                        {"label": "Start", "value": "start"},
                        {"label": "Stop", "value": "stop"},
                        {"label": "Restart", "value": "restart"},
                    ],
                    placeholder="Select action"
                ),
                html.Button("Execute", id=f"btn-{name}", n_clicks=0)
            ], style={"marginBottom": "20px"}))
    else:
        layout.extend([
            html.H5("Agent Control Panel"),
            dcc.Dropdown(
                id="multi-agent-dropdown",
                options=[{"label": k, "value": k} for k in agents],
                placeholder="Select an agent"
            ),
            html.Div(id="multi-agent-status"),
            dcc.Dropdown(
                id="multi-action-dropdown",
                options=[
                    {"label": "Start", "value": "start"},
                    {"label": "Stop", "value": "stop"},
                    {"label": "Restart", "value": "restart"},
                ],
                placeholder="Select action"
            ),
            html.Button("Execute", id="multi-agent-btn", n_clicks=0)
        ])

    return html.Div(layout)

def register_callbacks(app):
    @app.callback(
        Output("multi-agent-status", "children"),
        Input("multi-agent-btn", "n_clicks"),
        State("multi-agent-dropdown", "value"),
        State("multi-action-dropdown", "value"),
        prevent_initial_call=True
    )
    def handle_multi(n, agent_name, action):
        if not agent_name or not action:
            return "Select agent and action"
        result = control_agent(agent_name, action)
        logging.info("[AdminPanel] " + json.dumps({"TYPE": f"{action.upper()} for {agent_name}: {result}"}))
        return f"{agent_name}: {result}"

    for agent_name in get_registered_agents():
        app.callback(
            Output(f"status-{agent_name}", "children"),
            Input(f"btn-{agent_name}", "n_clicks"),
            State(f"action-{agent_name}", "value"),
            prevent_initial_call=True
        )(make_agent_callback(agent_name))

def make_agent_callback(agent_name):
    def callback(n_clicks, selected_action):
        if not selected_action:
            return f"Status: No action selected"
        result = control_agent(agent_name, selected_action)
        logging.info("[AdminPanel] " + json.dumps({"INDEX": agent_name.upper(), "TYPE": f"{selected_action.upper()} for {agent_name}: {result}"}))
        return f"Status: {result}"
    return callback
