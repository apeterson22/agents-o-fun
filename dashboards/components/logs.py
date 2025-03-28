from dash import html
TAB_ID = "logs"
TAB_LABEL = "Logs Viewer"

def render_layout():
    return html.Div([
        html.H3("Log Viewer"),
        html.P("Monitor logs for each component.")
    ])

def register_callbacks(app):
    pass