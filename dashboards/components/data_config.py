import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import logging
from configs.config_loader import load_config, update_config

logger = logging.getLogger("DataConfigTab")

TAB_ID = "data-config"
TAB_LABEL = "Data Configurations"

class DataConfigTab:
    TAB_ID = TAB_ID
    TAB_LABEL = TAB_LABEL

    def render_layout(self):
        config = load_config()
        forex_api = config.get("data_feeds", {}).get("forex", {}).get("apiKey", "")
        crypto_api = config.get("data_feeds", {}).get("crypto", {}).get("apiKey", "")
        asset_universe = ", ".join(config.get("universe", []))
        
        layout = dbc.Container([
            html.H2("Data Feed Configuration", className="mb-4"),
            dbc.Form([
                dbc.FormGroup([
                    dbc.Label("Forex API Key", html_for="forex-api-key"),
                    dbc.Input(id="forex-api-key", type="text", placeholder="Enter Forex API Key", value=forex_api)
                ]),
                dbc.FormGroup([
                    dbc.Label("Crypto API Key", html_for="crypto-api-key"),
                    dbc.Input(id="crypto-api-key", type="text", placeholder="Enter Crypto API Key", value=crypto_api)
                ]),
                dbc.FormGroup([
                    dbc.Label("Asset Universe", html_for="asset-universe"),
                    dbc.Input(id="asset-universe", type="text", 
                              placeholder="Comma-separated symbols (e.g., AAPL, GOOGL, BTC-USD)", 
                              value=asset_universe)
                ]),
                dbc.Button("Update Configuration", id="update-config-btn", color="primary", n_clicks=0)
            ], inline=False),
            html.Div(id="config-update-status", className="mt-3")
        ], fluid=True)
        return layout

    def register_callbacks(self, app):
        @app.callback(
            Output("config-update-status", "children"),
            Input("update-config-btn", "n_clicks"),
            State("forex-api-key", "value"),
            State("crypto-api-key", "value"),
            State("asset-universe", "value"),
            prevent_initial_call=True
        )
        def update_config_callback(n_clicks, forex_key, crypto_key, universe_str):
            new_settings = {
                "data_feeds": {
                    "forex": {"apiKey": forex_key},
                    "crypto": {"apiKey": crypto_key}
                },
                "universe": [s.strip() for s in universe_str.split(",")] if universe_str else []
            }
            try:
                update_config(new_settings)
                logger.info("Dashboard: Configuration updated.")
                return dbc.Alert("Configuration updated successfully.", color="success")
            except Exception as e:
                logger.error("Dashboard: Failed to update configuration: %s", e)
                return dbc.Alert("Failed to update configuration.", color="danger")

_tab = DataConfigTab()
render_layout = _tab.render_layout
register_callbacks = _tab.register_callbacks

