# utils/db_init.py
import sqlite3
import logging
from pathlib import Path

def init_databases():
    db_paths = {
        "trades": "trades.db",
        "training": "training_data.db"
    }

    for name, path in db_paths.items():
        db_file = Path(path)
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        if name == "trades":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    symbol TEXT,
                    action TEXT,
                    price REAL,
                    quantity REAL,
                    tag TEXT
                );
            """)
        elif name == "training":
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS training_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    features TEXT,
                    label TEXT,
                    tag TEXT
                );
            """)

        conn.commit()
        conn.close()
        logging.info(f"Database initialized: {db_file}")


