# dashboards/components/__init__.py
import pkgutil
import importlib
import dashboards.components as components_pkg

def load_tab_components():
    tab_modules = []

    for loader, module_name, is_pkg in pkgutil.iter_modules(components_pkg.__path__):
        if module_name.startswith("_"):
            continue  # Skip private/internal
        module = importlib.import_module(f"{components_pkg.__name__}.{module_name}")
        if hasattr(module, "TAB_ID") and hasattr(module, "render_layout"):
            tab_modules.append(module)

    # Optional: sort by name or priority
    tab_modules.sort(key=lambda m: getattr(m, "TAB_ID", "zzz"))
    return tab_modules

