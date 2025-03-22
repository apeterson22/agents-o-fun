import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import requests
import threading
import logging
import configparser

external_stylesheets = [dbc.themes.FLATLY]  # Light mode theme

class MonitoringDashboard:
    def __init__(self, agent):
        self.agent = agent
        self.app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
        self.server = self.app.server
        self._setup_layout()
        self.rl_trainer = None
        self.genetic_optimizer = None
        self.feature_writer = None
        self.logger = logging.getLogger("MonitoringDashboard")

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

    def _get_model_options(self):
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')
            models = config.get('AI', 'available_models', fallback='deepseek-r1:8b,text-davinci-003').split(',')
            return [{'label': model.strip(), 'value': model.strip()} for model in models]
        except Exception as e:
            self.logger.error(f"Error reading models from config: {e}")
            return [{'label': 'deepseek-r1:8b', 'value': 'deepseek-r1:8b'}]

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
        ])

    def _settings_tab(self):
        return html.Div([
            html.H4("Settings", className="text-dark"),
            html.Label("Select Model:", className="text-dark"),
            dcc.Dropdown(
                id='model-selector',
                options=self._get_model_options(),
                value=self.agent.config.get('AI', 'model', fallback='deepseek-r1:8b'),
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

        @self.app.callback(Output('init-modules-btn', 'n_clicks'), Input('init-modules-btn', 'n_clicks'))
        def init_modules(n):
            if n:
                try:
                    self.agent.initialize_modules()
                except Exception as e:
                    self.logger.error(f"Admin action failed: {e}")
            return 0

        @self.app.callback(Output('switch-model-btn', 'n_clicks'), [Input('switch-model-btn', 'n_clicks')], [State('model-selector', 'value')])
        def switch_model(n, selected_model):
            if n and selected_model:
                try:
                    self.agent.config.set('AI', 'model', selected_model)
                    with open('config.ini', 'w') as configfile:
                        self.agent.config.write(configfile)
                    self.agent._init_ai_client()
                except Exception as e:
                    self.logger.error(f"Model switch failed: {e}")
            return 0

