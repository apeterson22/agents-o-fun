# tests/test_dashboard_tabs.py

import importlib
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# List of component modules to test for presence of required functions
tabs = [
    "dashboards.components.overview",
    "dashboards.components.admin",
    "dashboards.components.training",
    "dashboards.components.analytics",
    "dashboards.components.database",
    "dashboards.components.logs",
    "dashboards.components.trading",
    "dashboards.components.network_monitoring",
]

@pytest.mark.parametrize("module_path", tabs)
def test_tab_module_structure(module_path):
    module = importlib.import_module(module_path)
    assert hasattr(module, "TAB_ID")
    assert hasattr(module, "TAB_LABEL")
    assert hasattr(module, "render_layout")
    assert callable(module.render_layout)
    assert hasattr(module, "register_callbacks")

