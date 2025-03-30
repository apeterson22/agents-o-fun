# dashboards/components/training.py

from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from dashboards.state import dashboard_state
from core.agent_registry import get_registered_agents
from utils.training_data import fetch_agent_training_stats

TAB_LABEL = "Training"
TAB_ID = "training"

def layout():
    agent_names = list(get_registered_agents().keys())
    return dbc.Container([
        html.H2("Training Performance"),
        dcc.Dropdown(
            id="training-agent-selector",
            options=[{"label": name.upper(), "value": name} for name in agent_names],
            value=agent_names[0] if agent_names else None,
            clearable=False,
        ),
        dcc.Interval(id="training-refresh", interval=5 * 1000, n_intervals=0),
        dbc.Row([
            dbc.Col(dcc.Graph(id="training-loss-graph"), width=6),
            dbc.Col(dcc.Graph(id="training-policy-graph"), width=6),
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id="training-timesteps-graph"), width=12),
        ])
    ], fluid=True)

def register_callbacks(app):
    @app.callback(
        [Output("training-loss-graph", "figure"),
         Output("training-policy-graph", "figure"),
         Output("training-timesteps-graph", "figure")],
        [Input("training-refresh", "n_intervals"),
         Input("training-agent-selector", "value")]
    )
    def update_training_graphs(n, agent_name):
        if not agent_name:
            return go.Figure(), go.Figure(), go.Figure()

        df = fetch_agent_training_stats(agent_name)
        if df.empty:
            return go.Figure(), go.Figure(), go.Figure()

        loss_fig = go.Figure(data=[
            go.Scatter(x=df["timestamp"], y=df["loss"], mode="lines", name="Loss")
        ])
        policy_fig = go.Figure(data=[
            go.Scatter(x=df["timestamp"], y=df["policy_gradient_loss"], mode="lines", name="Policy Gradient Loss")
        ])
        timestep_fig = go.Figure(data=[
            go.Scatter(x=df["timestamp"], y=df["total_timesteps"], mode="lines+markers", name="Timesteps")
        ])

        return loss_fig, policy_fig, timestep_fig

# Exports for the dashboard system
def render_layout():
    return layout()

