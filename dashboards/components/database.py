from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import sqlite3
import pandas as pd
import plotly.graph_objs as go

TAB_ID = "database"
TAB_LABEL = "Database"

DB_PATHS = {
    "training_data": "training_data.db",
    "trades": "trades.db",
    "network_traffic": "databases/network_traffic.db",
}

def render_layout():
    return html.Div([
        html.H3("Database Explorer"),
        dbc.Row([
            dbc.Col([
                html.Label("Select Database"),
                dcc.Dropdown(
                    id="db-dropdown",
                    options=[{"label": name.title().replace("_", " "), "value": path} for name, path in DB_PATHS.items()],
                    value="training_data.db",
                    clearable=False
                ),
                html.Label("Or enter custom SQL query"),
                dcc.Textarea(id="sql-input", style={"width": "100%", "height": "100px"}),
                html.Button("Run Query", id="run-query-btn", className="btn btn-primary mt-2")
            ], width=4),
            dbc.Col([
                html.Div(id="db-output")
            ], width=8),
        ])
    ], className="p-4")

def register_callbacks(app):
    @app.callback(
        Output("db-output", "children"),
        Input("run-query-btn", "n_clicks"),
        State("db-dropdown", "value"),
        State("sql-input", "value"),
        prevent_initial_call=True
    )
    def run_query(n_clicks, db_file, sql):
        if not sql:
            return html.Div("Please enter a SQL query.", className="text-warning")
        try:
            conn = sqlite3.connect(db_file)
            df = pd.read_sql_query(sql, conn)
            conn.close()
            if df.empty:
                return html.Div("✅ Query executed, but no results.")
            return dcc.Graph(
                figure=go.Figure(
                    data=[go.Table(
                        header=dict(values=list(df.columns), fill_color='paleturquoise', align='left'),
                        cells=dict(values=[df[col] for col in df.columns], fill_color='lavender', align='left')
                    )]
                )
            )
        except Exception as e:
            return html.Div(f"❌ Error: {e}", className="text-danger")

