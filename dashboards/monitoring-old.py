# dashboards/monitoring.py
import logging
from dash import Dash, html
import dash_bootstrap_components as dbc
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
        tab_elements = [
            html.Li(html.A(tab.TAB_LABEL, href=f"#{tab.TAB_ID}", className="nav-link"), className="nav-item")
            for tab in self.tabs
        ]
        tab_content = [
            html.Div(id=tab.TAB_ID, children=tab.render_layout(), className="tab-pane fade")
            for tab in self.tabs
        ]
        return html.Div([
            html.Ul(tab_elements, className="nav nav-tabs mb-3"),
            html.Div(tab_content, className="tab-content p-3")
        ], className="container-fluid")

    def _register_callbacks(self):
        for tab in self.tabs:
            try:
                if hasattr(tab, "register_callbacks"):
                    tab.register_callbacks(self.app)
                    logging.info(f"[MonitoringDashboard] Registered callbacks for tab {tab.TAB_ID}")
            except Exception as e:
                logging.error(f"[MonitoringDashboard] Error registering callbacks for tab {tab.TAB_ID}: {e}")

def launch_dashboard(agent_manager=None, host="0.0.0.0", port=8050):
    dashboard = MonitoringDashboard(agent_manager=agent_manager)
    logging.info(f"[MonitoringDashboard] Launching dashboard on http://{host}:{port}")
    dashboard.app.run(debug=False, host=host, port=port)
    logging.info("[MonitoringDashboard] Dashboard launched successfully")
