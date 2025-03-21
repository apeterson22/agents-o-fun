import os
import sqlite3
import json
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
import pandas as pd
import numpy as np

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
        self.logger = logging.getLogger(__name__)
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._init_db()
            self.logger.info("Training database initialized.")
        except Exception as e:
            self.logger.error(f"Failed to initialize training DB: {e}")

    def _init_db(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    tag TEXT,
                    data TEXT,
                    source TEXT,
                    tag TEXT,
                    sample TEXT
                )
            ''')

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

            elif mode == "market_bias":
                entry["market"] = "stocks"
                entry["bias"] = "market_bias"

            samples.append(entry)
        self.logger.info(f"{count} synthetic samples generated using mode '{mode}'.")
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
            self.logger.error(f"Failed to load real trades: {e}")
            return []

    def get_samples_by_tag(self, tag: str = "default") -> List[Dict[str, Any]]:
        """Retrieve all training samples by a given tag."""
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT sample FROM training_samples WHERE tag = ?", (tag,))
                rows = cursor.fetchall()
                samples = [json.loads(row[0]) for row in rows]
                self.logger.info(f"Retrieved {len(samples)} samples with tag '{tag}'.")
                return samples
        except Exception as e:
            self.logger.error(f"Error retrieving samples by tag '{tag}': {e}")
            return []

    def store_training_data(self, samples: List[Dict[str, Any]], tag: str = "default"):
        """Store a list of training samples in the database with a given tag."""
        try:
            with self.conn:
                timestamp = datetime.utcnow().isoformat()
                for sample in samples:
                    # Ensure all numpy data types are converted to native Python types
                    cleaned_sample = json.loads(json.dumps(sample, default=self._json_serializer))
                    self.conn.execute(
                        "INSERT INTO training_samples (tag, timestamp, data, source, sample) VALUES (?, ?, ?, ?, ?)",
                        (tag, timestamp, json.dumps(cleaned_sample))
                    )
            self.logger.info(f"Stored {len(samples)} samples under tag '{tag}'.")
        except Exception as e:
            self.logger.error(f"Error storing samples: {e}")

    def _json_serializer(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return str(obj)

    def get_available_tags(self) -> List[str]:
        """Return all distinct tags in the training set."""
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT DISTINCT tag FROM training_samples")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get available tags: {e}")
            return []

    def get_sample_count_by_tag(self) -> Dict[str, int]:
        """Return sample count for each tag for dashboard preview."""
        try:
            with self.conn:
                cursor = self.conn.execute("SELECT tag, COUNT(*) FROM training_samples GROUP BY tag")
                return {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            self.logger.error(f"Failed to get sample count by tag: {e}")
            return {}

    def export_batch_to_file(self, tag: str, batch: List[Dict]):
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(EXPORT_DIR, f"batch_{tag}_{timestamp}.json")
        with open(filename, 'w') as f:
            json.dump(batch, f, indent=4)
        self.logger.info(f"Exported batch '{tag}' to {filename}")

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

        with self.conn:
            cursor = self.conn.execute(query, params)
            rows = cursor.fetchall()
            return [json.loads(row[0]) for row in rows]

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

