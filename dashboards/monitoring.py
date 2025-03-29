import dash
from dash import html, dcc, Input, Output
from dashboards.components import load_tab_components

external_stylesheets = ['https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css']

class MonitoringDashboard:
    def __init__(self):
        self.app = dash.Dash(
            __name__,
            external_stylesheets=external_stylesheets,
            suppress_callback_exceptions=True
        )
        self.server = self.app.server
        self.tab_modules = load_tab_components()
        self._setup_layout()
        self._register_callbacks()

    def _setup_layout(self):
        self.app.layout = html.Div([
            dcc.Tabs(
                id="tabs",
                value=self.tab_modules[0].TAB_ID,
                children=[dcc.Tab(label=m.TAB_LABEL, value=m.TAB_ID) for m in self.tab_modules]
            ),
            html.Div(id="tab-content"),
        ])

    def _register_callbacks(self):
        @self.app.callback(Output("tab-content", "children"), Input("tabs", "value"))
        def render_tab(tab_id):
            for module in self.tab_modules:
                if module.TAB_ID == tab_id:
                    return module.render_layout()
            return html.Div(["Unknown tab."])

        for module in self.tab_modules:
            if hasattr(module, "register_callbacks"):
                module.register_callbacks(self.app)

    def run(self, **kwargs):
        self.app.run(**kwargs)

def launch_dashboard(**kwargs):
    dashboard = MonitoringDashboard()
    dashboard.run(**kwargs)

if __name__ == "__main__":
    launch_dashboard(debug=True, host='0.0.0.0', port=8050)
