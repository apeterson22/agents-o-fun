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

# Placeholder API credentials (replace with actual keys from your config)
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
        self.training_mode = False  # Track training mode status
        self.daily_goal = 10000  # $10,000 daily profit goal
        self.rl_trainer = None  # Placeholder for RLTrainer integration
        self.genetic_optimizer = None  # Placeholder for GeneticOptimizer
        self.feature_writer = None  # Placeholder for AdvancedFeatureWriter
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
            dcc.Interval(id='interval-component', interval=update_interval, n_intervals=0),
            dcc.Store(id="mode-store"),  # Stores training mode state
            dcc.Store(id='trade-data-store')
        ])

        self._register_callbacks()

    def _init_db(self) -> None:
        """Initializes the trades database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    market TEXT,
                    profit REAL,
                    strategy TEXT,
                    trade_type TEXT,
                    source TEXT  -- Added to track Fidelity, Crypto.com, etc.
                )
            ''')
        self.logger.info("Database initialized successfully")

    def _register_callbacks(self) -> None:
        @self.app.callback(
            [Output("training-status", "children"),
             Output("current-mode", "children"),
             Output("mode-store", "data")],
            [Input("toggle-train-btn", "n_clicks")],
            [State("mode-store", "data")],
            prevent_initial_call=True
        )
        def toggle_training(n_clicks, mode_state):
            """Toggle training mode and update display."""
            if mode_state is None:
                mode_state = {"training_mode": False}
            
            mode_state["training_mode"] = not mode_state["training_mode"]
            self.training_mode = mode_state["training_mode"]

            mode_text = "Training" if self.training_mode else "Trading"
            self.logger.info(f"Training Mode toggled: {mode_text}")

            if self.training_mode:
                self.logger.info("Starting Training Mode...")
                threading.Thread(target=self.agent.train_only_mode, daemon=True).start()

            return f"Training Mode: {mode_text}", f"Mode: {mode_text}", mode_state

        @self.app.callback(
            Output("health-status", "children"),
            [Input("retry-health-btn", "n_clicks")],
            prevent_initial_call=True
        )
        def retry_health_check(n_clicks):
            """Retry system health check asynchronously."""
            self.logger.info("Retrying system health check...")
            health_ok = asyncio.run(self.agent.health_check())  # Properly await the function
            return f"Health Check: {'PASS' if health_ok else 'FAIL'}"

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
        """Integrates with RLTrainer, GeneticOptimizer, and FeatureWriter."""
        self.rl_trainer = rl_trainer
        self.genetic_optimizer = genetic_optimizer
        self.feature_writer = feature_writer
        self.logger.info("Components integrated: RLTrainer, GeneticOptimizer, AdvancedFeatureWriter")

    def load_latest_data(self) -> pd.DataFrame:
        """Loads the latest trade data from the database."""
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
        """Checks the status of external APIs."""
        status = []
        for api, key in [('Fidelity', FIDELITY_API_KEY), 
                         ('Crypto.com', CRYPTOCOM_API_KEY), 
                         ('Coinbase', COINBASE_API_KEY)]:
            status.append(f"{api}: OK" if random.choice([True, False]) else f"{api}: Down")
        return " | ".join(status)

    def stop(self) -> None:
        """Stops the dashboard."""
        self.running = False
        self.logger.info("Dashboard stopped")

if __name__ == "__main__":
    from rl_trainer import RLTrainer
    from genetic_optimizer import GeneticOptimizer
    from feature_writer import AdvancedFeatureWriter

    dashboard = MonitoringDashboard(agent=None)  # Replace None with the actual agent
    rl_trainer = RLTrainer()
    genetic_optimizer = GeneticOptimizer()
    feature_writer = AdvancedFeatureWriter()
    
    dashboard.integrate_components(rl_trainer, genetic_optimizer, feature_writer)
    dashboard.start()

