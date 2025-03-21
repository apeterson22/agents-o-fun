import dash
from dash import dcc, html, Output, Input, State
import plotly.graph_objs as go
import pandas as pd
import threading
import time
import logging
import os
from typing import Dict, Any, List, Optional
from queue import Queue
import sqlite3
import asyncio
from datetime import datetime
import requests  # For API calls
import random  # For simulation (remove in production)
from ai_self_improvement.training_data_generator import get_training_sample_stats, TrainingDataGenerator
import json

FIDELITY_API_KEY = "your_fidelity_key"
CRYPTOCOM_API_KEY = "your_cryptocom_key"
COINBASE_API_KEY = "your_coinbase_key"

def setup_logging(log_file: str = 'logs/dashboard.log') -> logging.Logger:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        filemode='a'
    )
    return logging.getLogger(__name__)

class MonitoringDashboard:
    def __init__(self, agent, db_path: str = 'trades.db', update_interval: int = 1000) -> None:
        self.logger = setup_logging()
        self.agent = agent
        self.app = dash.Dash(__name__, update_title=None)
        self.trade_queue = Queue()
        self.db_path = db_path
        self.update_interval = update_interval
        self.running = False
        self.training_mode = False
        self.daily_goal = 10000
        self.rl_trainer = None
        self.genetic_optimizer = None
        self.feature_writer = None
        self._init_db()

        self.app.layout = html.Div([
            html.H1("AI Trading Dashboard - Agents-o-Fun", style={'textAlign': 'center'}),
            dcc.Graph(id='profit-graph'),
            dcc.Graph(id='strategy-performance'),
            dcc.Graph(id='market-breakdown'),
            html.Div(id='metrics', children=[
                html.H3("Key Metrics"),
                html.P(id='daily-profit'),
                html.P(id='goal-progress'),
                html.P(id='success-rate'),
                html.P(id='active-strategies'),
                html.P(id='api-status'),
                html.P(id="current-mode", children="Mode: Trading")
            ]),
            html.Button("Toggle Training Mode", id="toggle-train-btn", n_clicks=0),
            html.Button("Retry Health Check", id="retry-health-btn", n_clicks=0),
            html.Div(id="training-status"),
            html.Div(id="health-status"),
            dcc.Dropdown(
                id="training-mode-select",
                options=[
                    {"label": "Default", "value": "default"},
                    {"label": "Anomaly Injection", "value": "anomaly"},
                    {"label": "Market Bias", "value": "market_bias"}
                ],
                value="default",
                placeholder="Select Training Mode"
            ),
            html.Button("Generate Custom Training Set", id="custom-generate-btn"),

            html.H4("🧠 Training Sample Manager"),
            dcc.Dropdown(id="sample-tag-dropdown", options=[], placeholder="Choose a tag"),
            html.Button("Refresh Samples", id="refresh-samples-btn", n_clicks=0),
            html.Div(id="sample-preview-panel", style={"whiteSpace": "pre-wrap", "border": "1px solid #ccc", "padding": "1rem", "borderRadius": "10px"}),

            html.Div([
                html.H4("Training Data Overview"),
                html.Div(id='training-data-stats'),
                html.Button("Generate New Training Set", id="generate-training-btn", n_clicks=0),
                dcc.Interval(id="training-data-refresh", interval=60*1000, n_intervals=0)
            ]),
            dcc.Interval(id='interval-component', interval=update_interval, n_intervals=0),
            dcc.Store(id="mode-store"),
            dcc.Store(id='trade-data-store')
        ])

        self._register_callbacks()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    market TEXT,
                    profit REAL,
                    strategy TEXT,
                    trade_type TEXT,
                    source TEXT
                )
            ''')
        self.logger.info("Database initialized successfully")

    def _register_callbacks(self) -> None:
        @self.app.callback(
            [Output("training-status", "children"),
             Output("current-mode", "children"),
             Output("mode-store", "data"),
             Output("training-data-stats", "children")],
            [Input("toggle-train-btn", "n_clicks"),
             Input("training-data-refresh", "n_intervals"),
             Input("generate-training-btn", "n_clicks")],
            [State("mode-store", "data")],
            prevent_initial_call=True
        )
        def toggle_training(n_clicks, mode_state):
            if mode_state is None:
                mode_state = {"training_mode": False}
            mode_state["training_mode"] = not mode_state["training_mode"]
            self.training_mode = mode_state["training_mode"]

            mode_text = "Training" if self.training_mode else "Trading"
            self.logger.info(f"Training Mode toggled: {mode_text}")

            if self.training_mode:
                self.logger.info("Starting Training Mode...")
                threading.Thread(target=self.agent.train_only_mode, daemon=True).start()

            stats = get_training_sample_stats()
            return f"Training Mode: {mode_text}", f"Mode: {mode_text}", mode_state, html.Ul([
                html.Li(f"Total Samples: {stats['total_samples']}"),
                html.Li("By Tag:"),
                html.Ul([html.Li(f"{tag}: {count}") for tag, count in stats["tags"].items()])
            ])

        @self.app.callback(
            Output("sample-tag-dropdown", "options"),
            Input("refresh-samples-btn", "n_clicks"),
            prevent_initial_call=True
        )
        def update_tag_dropdown(_):
            try:
                tags = self.agent.training_data_generator.get_available_tags()
                return [{"label": tag, "value": tag} for tag in tags]
            except Exception as e:
                return []

        @self.app.callback(
            Output("sample-preview-panel", "children"),
            Input("refresh-samples-btn", "n_clicks"),
            State("sample-tag-dropdown", "value")
        )
        def display_sample_preview(n_clicks, selected_tag):
            if not selected_tag:
                return "No tag selected."

            samples = self.agent.training_data_generator.get_samples_by_tag(selected_tag)
            preview = samples[:5]
            return f"Total Samples: {len(samples)}\nPreview:\n{json.dumps(preview, indent=2)}"

    def start(self) -> None:
        if not self.running:
            self.running = True
            threading.Thread(target=self.run_dashboard, daemon=True).start()
            self.logger.info("Dashboard thread started")

    def run_dashboard(self) -> None:
        try:
            self.logger.info("Starting monitoring dashboard on http://0.0.0.0:8050")
            self.app.run_server(debug=False, host='0.0.0.0', port=8050, threaded=True)
        except Exception as e:
            self.logger.error(f"Dashboard server failed: {e}")
        finally:
            self.running = False

    def integrate_components(self, rl_trainer, genetic_optimizer, feature_writer) -> None:
        self.rl_trainer = rl_trainer
        self.genetic_optimizer = genetic_optimizer
        self.feature_writer = feature_writer
        self.logger.info("Components integrated: RLTrainer, GeneticOptimizer, AdvancedFeatureWriter")

    def load_latest_data(self) -> pd.DataFrame:
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM trades ORDER BY timestamp DESC LIMIT 1000", conn)
            if df.empty:
                return pd.DataFrame(columns=['timestamp', 'market', 'profit', 'strategy', 'trade_type', 'source'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            self.logger.error(f"Failed to load trade data: {e}")
            return pd.DataFrame(columns=['timestamp', 'market', 'profit', 'strategy', 'trade_type', 'source'])

    def _check_api_status(self) -> str:
        status = []
        for api, key in [('Fidelity', FIDELITY_API_KEY), 
                         ('Crypto.com', CRYPTOCOM_API_KEY), 
                         ('Coinbase', COINBASE_API_KEY)]:
            status.append(f"{api}: OK" if random.choice([True, False]) else f"{api}: Down")
        return " | ".join(status)

    def stop(self) -> None:
        self.running = False
        self.logger.info("Dashboard stopped")

if __name__ == "__main__":
    from rl_trainer import RLTrainer
    from genetic_optimizer import GeneticOptimizer
    from feature_writer import AdvancedFeatureWriter

    dashboard = MonitoringDashboard(agent=None)
    rl_trainer = RLTrainer()
    genetic_optimizer = GeneticOptimizer()
    feature_writer = AdvancedFeatureWriter()

    dashboard.integrate_components(rl_trainer, genetic_optimizer, feature_writer)
    dashboard.start()

