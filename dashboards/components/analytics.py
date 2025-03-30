# dashboards/components/analytics.py

from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dashboards.state import dashboard_state
from core.agent_registry import get_registered_agents
from utils.analytics_data import fetch_agent_analytics_stats

TAB_LABEL = "Analytics"
TAB_ID = "analytics"

def layout():
    agent_names = list(get_registered_agents().keys())
    return dbc.Container([
        html.H2("Analytics Dashboard"),
        dcc.Dropdown(
            id="analytics-agent-selector",
            options=[{"label": name.upper(), "value": name} for name in agent_names],
            value=agent_names[0] if agent_names else None,
            clearable=False
        ),
        dcc.Interval(id="analytics-refresh", interval=5 * 1000, n_intervals=0),
        dbc.Row([
            dbc.Col(html.Div(id="analytics-kpi-panel"), width=4),
            dbc.Col(dcc.Graph(id="analytics-performance-graph"), width=8),
        ])
    ], fluid=True)

def register_callbacks(app):
    @app.callback(
        Output("analytics-kpi-panel", "children"),
        [Input("analytics-refresh", "n_intervals"),
         Input("analytics-agent-selector", "value")]
    )
    def update_kpi_panel(n, agent_name):
        stats = fetch_agent_analytics_stats(agent_name)
        if not stats:
            return html.Div("No data available")

        return dbc.Card([
            dbc.CardHeader(f"KPIs - {agent_name.upper()}"),
            dbc.CardBody([
                html.P(f"Total Trades: {stats.get('trade_count', 0)}"),
                html.P(f"Prediction Accuracy: {stats.get('accuracy', 0):.2f}%"),
                html.P(f"Avg Reward: {stats.get('avg_reward', 0):.2f}"),
                html.P(f"Active Status: {stats.get('status', 'unknown')}"),
            ])
        ])

    @app.callback(
        Output("analytics-performance-graph", "figure"),
        [Input("analytics-refresh", "n_intervals"),
         Input("analytics-agent-selector", "value")]
    )
    def update_graph(n, agent_name):
        df = fetch_agent_analytics_stats(agent_name, as_df=True)
        if df.empty:
            return go.Figure()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["reward"], mode="lines+markers", name="Reward"))
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["accuracy"], mode="lines+markers", name="Accuracy"))
        return fig

# Export standard
def render_layout():
    return layout()

