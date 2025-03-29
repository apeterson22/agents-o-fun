import pandas as pd

def fetch_agent_training_stats(agent_name):
    # Replace this with real DB call
    try:
        return pd.read_csv(f"training_exports/{agent_name}_training.csv")
    except Exception:
        return pd.DataFrame()

