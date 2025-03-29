import pandas as pd

def fetch_agent_analytics_stats(agent_name, as_df=False):
    try:
        df = pd.read_csv(f"training_exports/{agent_name}_analytics.csv")
        if as_df:
            return df
        latest = df.iloc[-1]
        return {
            "trade_count": latest.get("trades", 0),
            "accuracy": latest.get("accuracy", 0),
            "avg_reward": latest.get("reward", 0),
            "status": latest.get("status", "unknown")
        }
    except Exception:
        return {} if not as_df else pd.DataFrame()

