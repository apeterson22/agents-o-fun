# dashboards/components/__init__.py
from dashboards.components.admin import AdminTab
from dashboards.components.training import TrainingTab
from dashboards.components.trading import TradingTab
from dashboards.components.decision_engine import DecisionEngineTab
from dashboards.components.data_config import DataConfigTab
from dashboards.components.network_monitoring import NetworkMonitoringTab
from dashboards.components.overview import OverviewTab
from dashboards.components.analytics import layout as analytics_layout, register_callbacks as analytics_callbacks
from dashboards.components.logs import render_layout as logs_layout, register_callbacks as logs_callbacks

def load_tab_components(agent_manager=None):
    return [
        AdminTab(agent_manager=agent_manager),
        DataConfigTab(),
        TradingTab(),
        TrainingTab(),
        DecisionEngineTab(agent_manager=agent_manager),
        NetworkMonitoringTab(agent_manager=agent_manager),
        OverviewTab(agent_manager=agent_manager),
        # For analytics and logs, you may wrap in a simple object that provides TAB_ID and TAB_LABEL:
        type("AnalyticsTab", (), {"TAB_ID": "analytics", "TAB_LABEL": "Analytics", "render_layout": analytics_layout, "register_callbacks": analytics_callbacks}),
        type("LogsTab", (), {"TAB_ID": "logs", "TAB_LABEL": "Logs Viewer", "render_layout": logs_layout, "register_callbacks": logs_callbacks}),
    ]

