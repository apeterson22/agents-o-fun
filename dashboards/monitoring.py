import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
import threading
import logging
import configparser
import json
import os
import sqlite3
import pandas as pd
import subprocess
import numpy as np

external_stylesheets = [dbc.themes.FLATLY]  # Light mode theme

DB_PATH = os.path.join("databases", "training_data.db")
CONFIG_DB_PATH = os.path.join("databases", "configurations.db")
TRADE_DB_PATH = os.path.join("databases", "trades.db")

class MonitoringDashboard:
    def __init__(self, agent):
        self.agent = agent
        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
        self.server = self.app.server
        self.logger = logging.getLogger("MonitoringDashboard")
        self._setup_layout()
        self.rl_trainer = None
        self.genetic_optimizer = None
        self.feature_writer = None
        self._initialize_all_databases()
        if not self._has_test_data():
            self._inject_test_data()

    def _initialize_all_databases(self):
        self._initialize_db(CONFIG_DB_PATH, [
            "CREATE TABLE IF NOT EXISTS configurations (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, key TEXT NOT NULL, value TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS config_history (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, config TEXT)",
            "CREATE TABLE IF NOT EXISTS schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER)"
        ], current_version=1)

        self._initialize_db(DB_PATH, [
            "CREATE TABLE IF NOT EXISTS training_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, step INTEGER, reward REAL, loss REAL)",
            "CREATE TABLE IF NOT EXISTS training_samples (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, model_name TEXT, strategy TEXT, tag TEXT)",
            "CREATE TABLE IF NOT EXISTS schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER)"
        ], current_version=2)

        self._initialize_db(TRADE_DB_PATH, [
            "CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, symbol TEXT, price REAL, volume INTEGER, result TEXT)",
            "CREATE TABLE IF NOT EXISTS schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER)"
        ], current_version=1)

    def _initialize_db(self, db_path, schema_statements, current_version=1):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (id INTEGER PRIMARY KEY CHECK (id = 1), version INTEGER)")
            cursor.execute("SELECT version FROM schema_version WHERE id = 1")
            row = cursor.fetchone()
            if row is None:
                for stmt in schema_statements:
                    try:
                        cursor.execute(stmt)
                    except sqlite3.OperationalError as se:
                        if "duplicate column name" in str(se):
                            self.logger.warning(f"Column already exists, skipping statement: {stmt}")
                        else:
                            raise
                cursor.execute("INSERT OR REPLACE INTO schema_version (id, version) VALUES (1, ?)", (current_version,))
                conn.commit()
                self.logger.info(f"Initialized {db_path} at schema version {current_version}")
            elif row[0] < current_version:
                self.logger.info(f"Database at {db_path} needs migration from v{row[0]} to v{current_version}")
                self._apply_migrations(cursor, row[0], current_version, db_path)
                conn.commit()
            if db_path == DB_PATH:
                cursor.execute("PRAGMA table_info(training_samples)")
                cols = [r[1] for r in cursor.fetchall()]
                for col in ["model_name", "strategy", "tag"]:
                    if col not in cols:
                        cursor.execute(f"ALTER TABLE training_samples ADD COLUMN {col} TEXT")
                conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to initialize DB schema at {db_path}: {e}")

    def _apply_migrations(self, cursor, current_version, target_version, db_path):
        if db_path == DB_PATH and current_version < 2:
            try:
                existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(training_samples)")]
                if "model_name" not in existing_cols:
                    cursor.execute("ALTER TABLE training_samples ADD COLUMN model_name TEXT")
                if "strategy" not in existing_cols:
                    cursor.execute("ALTER TABLE training_samples ADD COLUMN strategy TEXT")
                if "tag" not in existing_cols:
                    cursor.execute("ALTER TABLE training_samples ADD COLUMN tag TEXT")
                cursor.execute("UPDATE schema_version SET version = 2 WHERE id = 1")
                self.logger.info("Migrated training_data.db to schema version 2")
            except sqlite3.OperationalError as e:
                self.logger.warning(f"Migration skipped due to error: {e}")

    def _has_test_data(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM training_samples")
                sample_count = cursor.fetchone()[0]
            with sqlite3.connect(TRADE_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM trades")
                trade_count = cursor.fetchone()[0]
            return sample_count > 0 and trade_count > 0
        except:
            return False

    def _inject_test_data(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO training_samples (model_name, strategy, tag) VALUES (?, ?, ?)",
                               ("deepseek-r1:8b", "mean-reversion", "test-sample"))
                conn.commit()

            with sqlite3.connect(TRADE_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO trades (symbol, price, volume, result) VALUES (?, ?, ?, ?)",
                               ("AAPL", 186.12, 25, "win"))
                conn.commit()

            self.logger.info("Test data injected into training_samples and trades.")
        except Exception as e:
            self.logger.warning(f"Test data injection failed: {e}")

    def _get_model_options(self):
        try:
            output = subprocess.check_output(["ollama", "list"]).decode("utf-8")
            models = []
            for line in output.strip().split("\n")[1:]:
                parts = line.split()
                if parts:
                    models.append({"label": parts[0], "value": parts[0]})
            if not any(m['value'].lower().startswith("deepseek") for m in models):
                models.append({"label": "deepseek-r1:8b (fallback)", "value": "deepseek-r1:8b"})
            return models
        except Exception as e:
            self.logger.error(f"Error fetching available models: {e}")
            return [{"label": "deepseek-r1:8b (fallback)", "value": "deepseek-r1:8b"}]

    def integrate_components(self, rl_trainer, genetic_optimizer, feature_writer):
        self.rl_trainer = rl_trainer
        self.genetic_optimizer = genetic_optimizer
        self.feature_writer = feature_writer
        self._ensure_trainer_methods()

    def _ensure_trainer_methods(self):
        if not hasattr(self.rl_trainer, 'reload_model'):
            def dummy_reload():
                self.logger.warning("reload_model() not implemented, stub called.")
            self.rl_trainer.reload_model = dummy_reload

        if not hasattr(self.rl_trainer, 'save_checkpoint'):
            def dummy_checkpoint():
                self.logger.warning("save_checkpoint() not implemented, stub called.")
            self.rl_trainer.save_checkpoint = dummy_checkpoint

    def _get_current_model(self):
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            return config.get('AI', 'model', fallback='deepseek-r1:8b')
        except Exception as e:
            self.logger.error(f"Error getting current model from config: {e}")
            return 'deepseek-r1:8b'

    def _store_model_config(self, model_name):
        try:
            conn = sqlite3.connect(CONFIG_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO configurations (key, value) VALUES (?, ?)", ("model", model_name))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to store model config to DB: {e}")

    def _fetch_config_history(self):
        try:
            conn = sqlite3.connect(CONFIG_DB_PATH)
            df = pd.read_sql_query("SELECT timestamp, key, value FROM configurations ORDER BY timestamp DESC", conn)
            conn.close()
            return html.Div([
                html.H5("Configuration Change History"),
                dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True, className="mt-2")
            ])
        except Exception as e:
            self.logger.error(f"Error fetching config history: {e}")
            return html.Div("Failed to load config history.")

    def _setup_layout(self):
        self.app.layout = dbc.Container([
            html.H1("AI Trading Agent Dashboard", className="text-center my-4 text-dark"),
            dcc.Tabs(id="tabs", value="overview", children=[
                dcc.Tab(label="Overview", value="overview", children=self._overview_tab()),
                dcc.Tab(label="Admin", value="admin", children=self._admin_tab()),
                dcc.Tab(label="Settings", value="settings", children=self._settings_tab())
            ]),
            dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0),
        ], fluid=True)

    def _overview_tab(self):
        return html.Div([
            dbc.Row([
                dbc.Col(dbc.Card([html.H4("Reward", id="reward", className="card-title text-center text-dark")]), width=3),
                dbc.Col(dbc.Card([html.H4("Loss", id="loss", className="card-title text-center text-dark")]), width=3),
                dbc.Col(dbc.Button("Start Training", id="start-training-btn", color="success", className="w-100"), width=2),
                dbc.Col(dbc.Button("Reload Model", id="reload-model-btn", color="info", className="w-100"), width=2),
                dbc.Col(dbc.Button("Save Checkpoint", id="checkpoint-btn", color="warning", className="w-100"), width=2),
            ], className="mb-4"),
            dbc.Row([
                dbc.Col(dcc.Graph(id="reward-graph"), width=6),
                dbc.Col(dcc.Graph(id="loss-graph"), width=6),
            ])
        ])

    def _admin_tab(self):
        return html.Div([
            html.H4("Admin Panel", className="text-dark"),
            dbc.Button("Initialize Modules", id="init-modules-btn", color="primary", className="my-2"),
            html.Div(id="config-history", className="mt-3"),
        ])

    def _settings_tab(self):
        return html.Div([
            html.H4("Settings", className="text-dark"),
            html.Label("Select Model:", className="text-dark"),
            dcc.Dropdown(
                id='model-selector',
                options=self._get_model_options(),
                value=self._get_current_model(),
                clearable=False
            ),
            dbc.Button("Switch Model", id="switch-model-btn", color="secondary", className="my-2"),
        ])

    def start(self):
        self._register_callbacks()
        self.app.run(debug=False, host="0.0.0.0", port=8050, use_reloader=False)

    def _register_callbacks(self):
        @self.app.callback(
            Output('reward', 'children'),
            Output('loss', 'children'),
            Output('reward-graph', 'figure'),
            Output('loss-graph', 'figure'),
            Input('interval-component', 'n_intervals')
        )
        def update_dashboard(n):
            try:
                summary_resp = requests.get("http://127.0.0.1:8081/stats")
                raw_stats_resp = requests.get("http://127.0.0.1:8081/stats/raw")
                summary = summary_resp.json()
                raw_stats = raw_stats_resp.json()

                if isinstance(summary, list):
                    summary = summary[0] if summary else {}
                if not isinstance(raw_stats, list):
                    raw_stats = []

                reward_val = summary.get("reward", "N/A")
                loss_val = summary.get("loss", "N/A")

                reward_trace = go.Scatter(
                    x=[s.get("step", 0) for s in raw_stats if isinstance(s, dict)],
                    y=[s.get("reward", 0) for s in raw_stats if isinstance(s, dict)],
                    mode='lines+markers', name='Reward')
                loss_trace = go.Scatter(
                    x=[s.get("step", 0) for s in raw_stats if isinstance(s, dict)],
                    y=[s.get("loss", 0) for s in raw_stats if isinstance(s, dict)],
                    mode='lines+markers', name='Loss')
                reward_fig = go.Figure(data=[reward_trace])
                reward_fig.update_layout(title="Reward over Time", xaxis_title="Step", yaxis_title="Reward")
                loss_fig = go.Figure(data=[loss_trace])
                loss_fig.update_layout(title="Loss over Time", xaxis_title="Step", yaxis_title="Loss")

                return f"Reward: {reward_val}", f"Loss: {loss_val}", reward_fig, loss_fig
            except Exception as e:
                self.logger.error(f"Dashboard update error: {e}")
                return "Reward: N/A", "Loss: N/A", go.Figure(), go.Figure()

        @self.app.callback(Output('start-training-btn', 'n_clicks'), Input('start-training-btn', 'n_clicks'))
        def trigger_training(n):
            if n:
                threading.Thread(target=self.agent._train_only_sync, daemon=True).start()
            return 0

        @self.app.callback(Output('reload-model-btn', 'n_clicks'), Input('reload-model-btn', 'n_clicks'))
        def reload_model(n):
            if n:
                try:
                    if hasattr(self.agent.rl_trainer, 'reload_model'):
                        self.agent.rl_trainer.reload_model()
                except Exception as e:
                    self.logger.error(f"Reload model failed: {e}")
            return 0

        @self.app.callback(Output('checkpoint-btn', 'n_clicks'), Input('checkpoint-btn', 'n_clicks'))
        def save_checkpoint(n):
            if n:
                try:
                    if hasattr(self.agent.rl_trainer, 'save_checkpoint'):
                        self.agent.rl_trainer.save_checkpoint()
                except Exception as e:
                    self.logger.error(f"Checkpoint save failed: {e}")
            return 0

        @self.app.callback(Output('init-modules-btn', 'n_clicks'), Input('init-modules-btn', 'n_clicks'), prevent_initial_call=True)
        def init_modules(n):
            if n:
                try:
                    self.agent.initialize_modules()
                except Exception as e:
                    self.logger.error(f"Admin action failed: {e}")
            return 0

        @self.app.callback(
            Output('switch-model-btn', 'n_clicks'),
            Input('switch-model-btn', 'n_clicks'),
            State('model-selector', 'value'),
            prevent_initial_call=True
        )
        def switch_model(n, selected_model):
            if n and selected_model:
                try:
                    self.agent.config.set('AI', 'model', selected_model)
                    with open('config.ini', 'w') as configfile:
                        self.agent.config.write(configfile)
                    self.agent._init_ai_client()
                    self._store_model_config(selected_model)
                except Exception as e:
                    self.logger.error(f"Model switch failed: {e}")
            return 0

        @self.app.callback(Output('config-history', 'children'), Input('tabs', 'value'))
        def update_config_history(tab_value):
            if tab_value == 'admin':
                return self._fetch_config_history()
            return dash.no_update

