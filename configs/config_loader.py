import yaml
import os
import logging

logger = logging.getLogger("ConfigLoader")

def load_config(config_path="configs/agents_config.yaml"):
    if not os.path.exists(config_path):
        logger.error("Config file not found: %s", config_path)
        return {}
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    logger.info("Config loaded from %s", config_path)
    return config

def update_config(new_settings, config_path="configs/agents_config.yaml"):
    """
    Update the configuration file with new_settings (a dict).
    """
    config = load_config(config_path)
    def recursive_update(d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = recursive_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    new_config = recursive_update(config, new_settings)
    with open(config_path, "w") as f:
        yaml.dump(new_config, f)
    logger.info("Config updated in %s", config_path)
    return new_config

