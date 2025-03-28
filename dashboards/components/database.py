from dash import html

TAB_ID = "database"
TAB_LABEL = "Database"

def render_layout():
    return html.Div([
        html.H3("Database View"),
        html.P("SQLite tables and schema introspection will appear here."),
        html.P("✅ Ready for integration with stats_tracker or training_samples.")
    ])

def register_callbacks(app):
    pass

