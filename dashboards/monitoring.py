import logging

try:
    from dash import Dash, html
    from dash.dependencies import Input, Output
    import dash_bootstrap_components as dbc
except ImportError as e:
    raise ImportError(
        "Dash and dash-bootstrap-components are required for the monitoring dashboard."
        " Install them with 'pip install dash dash-bootstrap-components'."
    ) from e

import dashboards.components as components_pkg

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

class MonitoringDashboard:
    def __init__(self, agent_manager=None):
        self.agent_manager = agent_manager
        self.app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.tabs = components_pkg.load_tab_components(agent_manager=self.agent_manager)
        self._register_callbacks()
        self.app.layout = self._render_layout()

    def _render_layout(self):
        tab_elements = [dbc.Tab(label=module.TAB_LABEL, tab_id=module.TAB_ID) for module in self.tabs]
        return dbc.Container([
            dbc.Tabs(id="tabs", active_tab=self.tabs[0].TAB_ID, children=tab_elements),
            html.Div(id="tab-content", className="mt-3")
        ], fluid=True)

    def _register_callbacks(self):
        @self.app.callback(
            Output("tab-content", "children"),
            [Input("tabs", "active_tab")]
        )
        def render_tab(active_tab):
            for module in self.tabs:
                if module.TAB_ID == active_tab:
                    return module.render_layout()
            return html.Div("Unknown tab.")
        # Register callbacks from each tab component
        for module in self.tabs:
            if hasattr(module, "register_callbacks"):
                try:
                    module.register_callbacks(self.app)
                    logging.info(f"[MonitoringDashboard] Registered callbacks for tab {module.TAB_ID}")
                except Exception as e:
                    logging.error(f"[MonitoringDashboard] Error registering callbacks for tab {module.TAB_ID}: {e}")

def launch_dashboard(agent_manager=None, host="0.0.0.0", port=8050):
    dashboard = MonitoringDashboard(agent_manager=agent_manager)
    logging.info(f"[MonitoringDashboard] Launching dashboard on http://{host}:{port}")
    dashboard.app.run_server(debug=False, host=host, port=port)
    logging.info("[MonitoringDashboard] Dashboard launched successfully")

if __name__ == "__main__":
    launch_dashboard()

