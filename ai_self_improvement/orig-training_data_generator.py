import os
import sqlite3
import json
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional, Union
import pandas as pd

TRAINING_DB = 'training_data.db'
EXPORT_DIR = 'training_exports'

os.makedirs(EXPORT_DIR, exist_ok=True)

logging.basicConfig(
    filename='logs/training_data_generator.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class TrainingDataGenerator:
    def __init__(self, db_path: str = TRAINING_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source TEXT,
                    tag TEXT,
                    sample TEXT
                )
            ''')
        logging.info("Training database initialized.")

    def generate_synthetic_samples(self, count: int = 100, mode: str = "default") -> List[Dict]:
        samples = []
        for _ in range(count):
            base_profit = random.uniform(-100, 300)
            entry = {
                "market": random.choice(["stocks", "crypto", "sports"]),
                "profit": base_profit,
                "strategy": random.choice(["momentum", "arbitrage", "ppo_rl"]),
                "trade_type": random.choice(["buy", "sell", "bet"]),
                "expected_return": base_profit * random.uniform(0.8, 1.2)
            }

            if mode == "anomaly":
                entry["profit"] *= random.choice([5, -5])
                entry["anomaly"] = True

            elif mode == ["market_bias"]:
                entry["market"] = "stocks"
                entry["bias"] = "market_bias"

            samples.append(entry)
        logging.info(f"{count} synthetic samples generated using mode '{mode}'.")
        return samples

    def fetch_real_trades(self, trade_db_path: str = 'trades.db', limit: int = 500) -> List[Dict]:
        try:
            with sqlite3.connect(trade_db_path) as conn:
                df = pd.read_sql_query(f"SELECT * FROM trades ORDER BY timestamp DESC LIMIT {limit}", conn)
            if df.empty:
                return []
            df = df.fillna('N/A')
            return df.to_dict('records')
        except Exception as e:
            logging.error(f"Failed to load real trades: {e}")
            return []

    def store_training_data(self, samples: List[Dict], tag: str = "general", source: str = "generated"):
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            for sample in samples:
                conn.execute(
                    "INSERT INTO training_samples (timestamp, source, tag, sample) VALUES (?, ?, ?, ?)",
                    (timestamp, source, tag, json.dumps(sample))
                )
        logging.info(f"Stored {len(samples)} training samples to DB under tag '{tag}'.")

    def export_batch_to_file(self, tag: str, batch: List[Dict]):
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(EXPORT_DIR, f"batch_{tag}_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump(batch, f, indent=4)
        logging.info(f"Exported batch '{tag}' to {filename}")

    def generate_and_store_all(self, synthetic_count: int = 200, trade_log_limit: int = 500, mode: str = "default") -> List[Dict]:
        real_trades = self.fetch_real_trades(limit=trade_log_limit)
        synthetic = self.generate_synthetic_samples(count=synthetic_count, mode=mode)
        full_batch = real_trades + synthetic
        self.store_training_data(full_batch, tag=mode)
        self.export_batch_to_file(tag=mode, batch=full_batch)
        return full_batch

    def retrieve_by_filter(self, tag: Optional[str] = None, source: Optional[str] = None, since: Optional[str] = None) -> List[Dict]:
        query = "SELECT sample FROM training_samples WHERE 1=1"
        params = []
        if tag:
            query += " AND tag = ?"
            params.append(tag)
        if source:
            query += " AND source = ?"
            params.append(source)
        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [json.loads(row[0]) for row in rows]

# Dashboard integration hook (to show count or preview on UI)
def get_training_sample_stats() -> Dict[str, Union[int, str]]:
    try:
        with sqlite3.connect(TRAINING_DB) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM training_samples")
            total = cursor.fetchone()[0]
            cursor = conn.execute("SELECT tag, COUNT(*) FROM training_samples GROUP BY tag")
            tags = {row[0]: row[1] for row in cursor.fetchall()}
            return {"total_samples": total, "tags": tags}
    except Exception as e:
        logging.error(f"Error retrieving training stats: {e}")
        return {"total_samples": 0, "tags": {}}

if __name__ == "__main__":
    tdg = TrainingDataGenerator()
    tdg.generate_and_store_all(synthetic_count=100, trade_log_limit=300, mode="market_bias")
    stats = get_training_sample_stats()
    print("Training sample summary:", stats)

