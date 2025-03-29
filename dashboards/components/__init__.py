import importlib
import pkgutil
from dashboards.components import overview, training, database, analytics, logs, admin, network_monitoring, trading

def load_tab_components():
    return [overview, training, database, analytics, admin, logs, network_monitoring, trading]

