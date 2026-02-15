import logging
import sqlite3
from pytrends.request import TrendReq
from datetime import datetime

log = logging.getLogger(__name__)
DB_PATH = "databases/training_data.db"
pd.set_option('future.no_silent_downcasting', True)

class MarketingAgent:
    def __init__(self, terms=None):
        self.pytrends = TrendReq()
        self.terms = terms or ["ai", "blockchain", "quantum computing"]

    def fetch_trends(self):
        self.pytrends.build_payload(self.terms, timeframe='now 1-d')
        df = self.pytrends.interest_over_time()
        if "isPartial" in df.columns:
            df = df.drop(columns=["isPartial"])
        return df

    def save_to_db(self, df):
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("google_trends", conn, if_exists="append", index=True)
        conn.close()

    def run(self):
        try:
            df = self.fetch_trends()
            self.save_to_db(df)
            log.info("MarketingAgent collected and saved trend data.")
        except Exception as e:
            log.error(f"MarketingAgent failed: {e}")
