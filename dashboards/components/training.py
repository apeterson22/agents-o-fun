from dash import html, dcc
from dash.dependencies import Input, Output
import random

TAB_ID = "training"
TAB_LABEL = "Training"

def render_layout():
    return html.Div([
        html.H3("Training Dashboard"),
        html.Div(id="training-status"),
        dcc.Interval(id="training-refresh", interval=7000, n_intervals=0)
    ])

def register_callbacks(app):
    @app.callback(
        Output("training-status", "children"),
        Input("training-refresh", "n_intervals")
    )
    def update_training_status(n):
        steps = random.randint(1000, 10000)
        loss = round(random.uniform(0.1, 1.2), 3)
        return html.Div([
            html.P(f"Training Steps: {steps}"),
            html.P(f"Current Loss: {loss}")
        ])

