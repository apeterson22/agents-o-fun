# utils/sample_data_injector.py
import sqlite3
import os
import logging
import random
from datetime import datetime, timedelta
from configs import paths

#DB_PATH = os.path.join("databases", "training_data.db")

def run_data_injection(num_records=300):
    try:
        conn = sqlite3.connect(paths.TRAINING_DATA_DB)
        c = conn.cursor()

        # Ensure the table has the correct columns
        c.execute("""
            CREATE TABLE IF NOT EXISTS training_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature1 REAL,
                feature2 REAL,
                feature3 REAL,
                label INTEGER,
                timestamp TEXT
            )
        """)

        now = datetime.utcnow()
        for _ in range(num_records):
            row = (
                random.uniform(-1, 1),
                random.uniform(0, 100),
                random.uniform(10, 500),
                random.randint(0, 2),
                (now + timedelta(seconds=random.randint(0, 10000))).isoformat()
            )
            c.execute("INSERT INTO training_samples (feature1, feature2, feature3, label, timestamp) VALUES (?, ?, ?, ?, ?)", row)

        conn.commit()
        conn.close()
        logging.info(f"{num_records} synthetic training samples injected.")
    except Exception as e:
        logging.error(f"Data injection failed: {str(e)}")

