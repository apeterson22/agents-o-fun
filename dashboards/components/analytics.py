from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import random
import numpy as np  # add this import at the top if not already present


TAB_ID = "analytics"
TAB_LABEL = "Analytics"

def render_layout():
    return html.Div([
        html.H3("Performance Analytics"),
        dcc.Graph(id="performance-graph"),
        dcc.Interval(id="analytics-refresh", interval=10000, n_intervals=0)
    ])

def register_callbacks(app):
    @app.callback(
        Output("performance-graph", "figure"),
        Input("analytics-refresh", "n_intervals")
    )
    def update_graph(_):
        df = pd.DataFrame({
            "Timestamp": pd.date_range(end=pd.Timestamp.now(), periods=20, freq="min"),
            "Profit": [random.uniform(-50, 100) for _ in range(20)]
        })

        # ✅ CORRECT way: use `.dt.to_pydatetime()` (not directly on the series)
        df["Timestamp"] = np.array(df["Timestamp"].dt.to_pydatetime())

        fig = px.line(
            df,
            x="Timestamp",
            y="Profit",
            title="📈 Simulated Trading Profit Over Time",
            markers=True
        )
        fig.update_layout(margin=dict(l=40, r=20, t=40, b=30))
        return fig

