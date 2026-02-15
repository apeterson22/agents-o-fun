import logging
from dash import html, dcc, Output, Input
import plotly.graph_objs as go
import sqlite3
import pandas as pd

TAB_ID = "trading"
TAB_LABEL = "Trading"

class TradingTab:
    TAB_ID = TAB_ID
    TAB_LABEL = TAB_LABEL

    def __init__(self):
        self.db_path = "databases/trades.db"  # Adjusted as needed

    def fetch_trades(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 1000", conn)
                logging.info(f"Fetched {len(df)} trades from {self.db_path}")
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                return df
        except Exception as e:
            logging.error(f"Error fetching trades: {e}")
            return pd.DataFrame()

    def render_layout(self):
        return html.Div([
            html.H3("Trading Dashboard", className="text-center my-3"),
            dcc.Graph(id="profit-graph"),
            dcc.Interval(id="trade-refresh", interval=5000, n_intervals=0),
        ])

    def register_callbacks(self, app):
        @app.callback(
            Output("profit-graph", "figure"),
            Input("trade-refresh", "n_intervals")
        )
        def update_profit_graph(n_intervals):
            df = self.fetch_trades()
            if df.empty:
                fig = go.Figure()
                fig.update_layout(title="No Trading Data Available")
            else:
                fig = go.Figure()
                for market in df["market"].unique():
                    market_df = df[df["market"] == market]
                    fig.add_trace(go.Scatter(
                        x=market_df["timestamp"],
                        y=market_df["profit"].cumsum(),
                        mode="lines",
                        name=f"{market} Profit",
                        hovertemplate="Time: %{x}<br>Profit: $%{y:.2f}"
                    ))
                fig.update_layout(
                    title="Cumulative Trading Profit",
                    xaxis_title="Time",
                    yaxis_title="Profit ($)",
                    legend_title="Market"
                )
            return fig

render_layout = TradingTab().render_layout
register_callbacks = TradingTab().register_callbacks

