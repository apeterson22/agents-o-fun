import importlib
import pkgutil
from dashboards.components import overview, training, database, analytics, logs, admin

def load_tab_components():
    return [overview, training, database, analytics, admin, logs]

