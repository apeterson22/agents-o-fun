
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from utils.stats_tracker import SharedStatsTracker

TAB_ID = "overview"
TAB_LABEL = "Overview"

def render_layout():
    stats = SharedStatsTracker.get_instance().get_latest()
    return html.Div([
        html.H3("System Overview", className="my-3"),
        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Training Status"),
                dbc.CardBody([
                    html.P(f"Timesteps: {stats.get('total_timesteps', 'N/A')}"),
                    html.P(f"Loss: {stats.get('loss', 'N/A')}"),
                    html.P(f"Entropy: {stats.get('entropy_loss', 'N/A')}"),
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardHeader("Agent Health"),
                dbc.CardBody(id="agent-health", children=[
                    html.P("Agent status: Active"),
                    html.P("Trade Count: 0"),
                ])
            ]), width=4),
            dbc.Col(dbc.Card([
                dbc.CardHeader("System Health"),
                dbc.CardBody([
                    html.P("CPU Load: OK"),
                    html.P("Memory: OK")
                ])
            ]), width=4),
        ]),
        dcc.Interval(id="health-refresh", interval=30*1000, n_intervals=0)
    ])

def register_callbacks(app):
    @app.callback(
        Output("agent-health", "children"),
        Input("health-refresh", "n_intervals")
    )
    def update_agent_health(n):
        stats = SharedStatsTracker.get_instance().get_latest()
        return [
            html.P(f"Agent status: Active"),
            html.P(f"Trade Count: {stats.get('trade_count', 0)}"),
        ]
