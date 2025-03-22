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
import requests
import random
from ai_self_improvement.training_data_generator import get_training_sample_stats, TrainingDataGenerator

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

            dcc.Tabs(id="tabs", value='tab-dashboard', children=[
                dcc.Tab(label='Dashboard', value='tab-dashboard'),
                dcc.Tab(label='Training Data', value='tab-training'),
                dcc.Tab(label='API Health', value='tab-health'),
                dcc.Tab(label='Logs', value='tab-logs'),
                dcc.Tab(label='Admin', value='tab-admin')
            ]),

            html.Div(id='tabs-content'),

            dcc.Interval(id='interval-component', interval=update_interval, n_intervals=0),
            dcc.Interval(id="logs-refresh", interval=5000, n_intervals=0),
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
            Output('tabs-content', 'children'),
            [Input('tabs', 'value'),
             Input("interval-component", "n_intervals"),
             Input("logs-refresh", "n_intervals")]
        )
        def update_tab_content(tab, *_):
            try:
                if tab == 'tab-dashboard':
                    return html.Div([
                        html.H3("Agent Status & Controls"),
                        html.Div([
                            html.Button("Toggle Training Mode", id="toggle-train-btn", n_clicks=0),
                            html.Button("Retry Health Check", id="retry-health-btn", n_clicks=0),
                            html.Button("Stop Dashboard", id="stop-dashboard-btn", n_clicks=0, style={'backgroundColor': 'red', 'color': 'white'})
                        ], style={'marginBottom': '20px'}),
                        html.Div(id="training-status"),
                        html.Div(id="health-status"),
                        html.H4(id="current-mode", children="Mode: Trading"),
                        dcc.Graph(id='profit-graph'),
                        dcc.Graph(id='strategy-performance'),
                        dcc.Graph(id='market-breakdown'),
                        html.Div(id='metrics', children=[
                            html.H3("Key Metrics"),
                            html.P(id='daily-profit'),
                            html.P(id='goal-progress'),
                            html.P(id='success-rate'),
                            html.P(id='active-strategies'),
                            html.P(id='api-status')
                        ])
                    ])

                elif tab == 'tab-training':
                    stats = get_training_sample_stats()
                    return html.Div([
                        html.H3("Training Data"),
                        html.Div([
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
                            html.Button("Generate Custom Training Set", id="custom-generate-btn")
                        ]),
                        html.Div(id='training-data-stats', children=html.Ul([
                            html.Li(f"Total Samples: {stats['total_samples']}"),
                            html.Li("By Tag:"),
                            html.Ul([html.Li(f"{tag}: {count}") for tag, count in stats["tags"].items()])
                        ]))
                    ])

                elif tab == 'tab-health':
                    return html.Div([
                        html.H3("Health Check & Component Status"),
                        html.Div(id="health-status"),
                        html.P("(Automatically updated every 5 seconds.)")
                    ])

                elif tab == 'tab-logs':
                    logs = self._tail_logs()
                    return html.Div([
                        html.H3("Live Logs"),
                        html.Pre(logs, style={"whiteSpace": "pre-wrap", "maxHeight": "600px", "overflowY": "scroll"})
                    ])

                elif tab == 'tab-admin':
                    return html.Div([
                        html.H3("Admin Controls"),
                        html.Button("Restart Agent", id="restart-agent-btn"),
                        html.Button("Restart Training Loop", id="restart-training-btn"),
                        html.Button("Restart All Modules", id="restart-all-btn"),
                        html.Div(id="admin-feedback")
                    ])
            except Exception as e:
                self.logger.error(f"Error rendering tab {tab}: {e}")
                return html.Div(f"Error loading {tab} tab.")

        @self.app.callback(
            Output("admin-feedback", "children"),
            [Input("restart-agent-btn", "n_clicks"),
             Input("restart-training-btn", "n_clicks"),
             Input("restart-all-btn", "n_clicks")],
            prevent_initial_call=True
        )
        def handle_admin_controls(agent_clicks, train_clicks, all_clicks):
            triggered = dash.ctx.triggered_id
            msg = ""
            try:
                if triggered == "restart-agent-btn":
                    msg = "Agent restarted."
                    threading.Thread(target=self.agent.trading_loop, daemon=True).start()
                elif triggered == "restart-training-btn":
                    msg = "Training loop restarted."
                    threading.Thread(target=self.agent.train_only_mode, daemon=True).start()
                elif triggered == "restart-all-btn":
                    msg = "All modules restarted."
                    threading.Thread(target=self.agent.initialize_modules, daemon=True).start()
                self.logger.info(msg)
                return msg
            except Exception as e:
                self.logger.error(f"Admin action failed: {e}")
                return f"Admin action failed: {e}"

    def start(self) -> None:
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self.run_dashboard, daemon=True)
            thread.start()
            self.logger.info("Dashboard thread started")

    def run_dashboard(self) -> None:
        try:
            self.logger.info("Starting monitoring dashboard on http://0.0.0.0:8050")
            self.app.run_server(debug=False, host='0.0.0.0', port=8050, threaded=True, use_reloader=False)
        except Exception as e:
            self.logger.error(f"Dashboard server failed: {e}")

    def integrate_components(self, rl_trainer, genetic_optimizer, feature_writer) -> None:
        self.rl_trainer = rl_trainer
        self.genetic_optimizer = genetic_optimizer
        self.feature_writer = feature_writer
        self.logger.info("Components integrated: RLTrainer, GeneticOptimizer, AdvancedFeatureWriter")

    def _tail_logs(self, lines: int = 200) -> str:
        log_dir = "logs"
        buffer = []
        try:
            for filename in os.listdir(log_dir):
                if filename.endswith(".log"):
                    path = os.path.join(log_dir, filename)
                    with open(path, 'r') as f:
                        content = f.readlines()[-lines:]
                        buffer.append(f"==== {filename} ====")
                        buffer.extend(content)
                        buffer.append("\n")
            return "\n".join(buffer)
        except Exception as e:
            self.logger.error(f"Error tailing logs: {e}")
            return "Unable to load logs."

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
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        dashboard.logger.info("Dashboard interrupted and shutting down gracefully")
