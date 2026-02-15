import pkgutil
import importlib

def load_tab_components(agent_manager=None):
    tab_modules = []
    # Iterate through all modules in the current package.
    for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):
        if module_name.startswith("_"):
            continue  # Skip private modules.
        module = importlib.import_module(f"dashboards.components.{module_name}")
        # Check if the module has TAB_ID and render_layout attributes.
        if hasattr(module, "TAB_ID") and hasattr(module, "render_layout"):
            tab_modules.append(module)
    # Optional: sort by TAB_ID (alphabetically, for instance).
    tab_modules.sort(key=lambda m: getattr(m, "TAB_ID", "zzz"))
    return tab_modules

