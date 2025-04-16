# dashboards/components/__init__.py
from .admin import AdminTab
from .decision_engine import DecisionEngineTab
from .network_monitoring import NetworkMonitoringTab
from .overview import OverviewTab

def load_tab_components(agent_manager=None):
    tabs = [
        AdminTab(agent_manager=agent_manager),
        DecisionEngineTab(agent_manager=agent_manager),
        NetworkMonitoringTab(agent_manager=agent_manager),
        OverviewTab(agent_manager=agent_manager),
    ]
    # Dynamically load other tabs (analytics, database, etc.)
    for tab in [
        ("analytics", "Analytics"),
        ("database", "Database"),
        ("logs", "Logs Viewer"),
        ("trading", "Trading"),
        ("training", "Training")
    ]:
        tab_id, tab_label = tab
        tabs.append(type('Tab', (), {
            'TAB_ID': tab_id,
            'TAB_LABEL': tab_label,
            'render_layout': lambda self: [f"Placeholder for {tab_label} tab"],
            'register_callbacks': lambda self, app: None  # Placeholder
        })())
    return tabs
