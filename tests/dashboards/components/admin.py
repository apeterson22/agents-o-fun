
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import logging

TAB_ID = "admin"
TAB_LABEL = "Admin"

logger = logging.getLogger("admin")

def render_layout():
    return html.Div([
        html.H3("Admin Panel"),
        dbc.Button("Inject Sample Data", id="inject-data-btn", color="primary", className="mb-2"),
        dbc.Button("Reset Trade Count", id="reset-trade-btn", color="danger", className="mb-2"),
        html.Div(id="admin-action-result"),
        dbc.Alert(id="admin-alert", is_open=False, duration=5000)
    ])

def register_callbacks(app):
    from utils.sample_data_injector import run_data_injection
    from core.regulatory_compliance import RegulatoryCompliance

    compliance = RegulatoryCompliance()

    @app.callback(
        Output("admin-alert", "children"),
        Output("admin-alert", "color"),
        Output("admin-alert", "is_open"),
        Input("inject-data-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def handle_data_injection(n_clicks):
        run_data_injection()
        logger.info("Injected synthetic data.")
        return "Synthetic data injected successfully.", "success", True

    @app.callback(
        Output("admin-action-result", "children"),
        Output("admin-alert", "children"),
        Output("admin-alert", "color"),
        Output("admin-alert", "is_open"),
        Input("reset-trade-btn", "n_clicks"),
        prevent_initial_call=True
    )
    def reset_trades(n_clicks):
        compliance.reset_trade_count()
        logger.info("Trade count reset via admin panel.")
        return "Trade count reset.", "Trade count has been reset.", "warning", True
