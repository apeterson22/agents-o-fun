# agents/trading_agent.py
import logging
import yfinance as yf
import sqlite3
import time
from datetime import datetime
from core.agent_registry import register_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger(__name__)
DB_PATH = "trades.db"

@register_agent("trading", description="Fetches and stores stock market data", model="Finance RL Model", data_source="Yahoo Finance")
class TradingAgent:
    def __init__(self, tickers=None, period="1d", interval="5m", fetch_count=5, continuous=False, run_interval=300):
        """
        Initialize the TradingAgent.

        Args:
            tickers (list): List of ticker symbols to fetch data for.
                           Defaults to ["AAPL", "GOOGL", "MSFT", "AMD", "TSLA"].
            period (str): Data period to fetch from yfinance. Defaults to "1d".
            interval (str): Data interval to fetch from yfinance. Defaults to "5m".
            fetch_count (int): Number of latest records to process per ticker.
            continuous (bool): If True, run continuously; otherwise run once.
            run_interval (int): Time in seconds between data collection cycles when running continuously.
        """
        self.tickers = tickers or ["AAPL", "GOOGL", "MSFT", "AMD", "TSLA"]
        self.period = period
        self.interval = interval
        self.fetch_count = fetch_count
        self.continuous = continuous
        self.run_interval = run_interval
        self.status = "initialized"
        self.last_error = None

    def fetch_stock_data(self):
        """
        Fetch recent stock data for each ticker.

        Returns:
            list: A list of dictionaries containing market data.
        """
        result = []
        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=self.period, interval=self.interval)
                if hist.empty:
                    log.warning(f"No data returned for {ticker}")
                    continue
                for index, row in hist.tail(self.fetch_count).iterrows():
                    record = {
                        "timestamp": index.to_pydatetime().isoformat(),
                        "ticker": ticker,
                        "open": row.get("Open"),
                        "high": row.get("High"),
                        "low": row.get("Low"),
                        "close": row.get("Close"),
                        "volume": int(row.get("Volume", 0)),
                        "fetched_at": datetime.utcnow().isoformat()
                    }
                    result.append(record)
                log.info(f"Fetched {self.fetch_count} records for {ticker}.")
            except Exception as e:
                log.error(f"Error fetching data for {ticker}: {e}")
                self.last_error = str(e)
        return result

    def save_to_db(self, entries):
        """
        Save market data entries into the database.

        The table 'live_trades' includes columns for open, high, low, close, volume, and a fetched_at timestamp.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS live_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    ticker TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    fetched_at TEXT
                )
            """)
            for e in entries:
                cursor.execute(
                    "INSERT INTO live_trades (timestamp, ticker, open, high, low, close, volume, fetched_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (e["timestamp"], e["ticker"], e["open"], e["high"], e["low"], e["close"], e["volume"], e["fetched_at"])
                )
            conn.commit()
            conn.close()
            log.info(f"Saved {len(entries)} records to the database.")
        except Exception as e:
            log.error(f"Error saving to DB: {e}")
            self.last_error = str(e)

    def collect_and_store_data(self):
        """
        Collect stock market data and store it in the database.
        """
        log.info("[TRADING AGENT] Starting data collection...")
        data = self.fetch_stock_data()
        if data:
            self.save_to_db(data)
            log.info("[TRADING AGENT] Data collection complete.")
        else:
            log.warning("[TRADING AGENT] No data fetched.")
            self.last_error = "No data fetched."

    def run(self):
        """
        Run the trading agent.

        If continuous mode is enabled, the agent collects data periodically.
        Otherwise, it performs a single data collection cycle.
        """
        self.status = "running"
        try:
            if self.continuous:
                log.info("[TRADING AGENT] Running in continuous mode.")
                while self.status == "running":
                    self.collect_and_store_data()
                    time.sleep(self.run_interval)
            else:
                self.collect_and_store_data()
        except Exception as e:
            log.error(f"[TRADING AGENT] Encountered an error: {e}")
            self.status = "error"
            self.last_error = str(e)

    def stop(self):
        """
        Stop the trading agent.
        """
        self.status = "stopped"
        log.info("[TRADING AGENT] Agent stopped.")

    def health_check(self):
        """
        Perform a health check on the agent.

        Returns:
            dict: Health status information.
        """
        return {
            "status": self.status,
            "last_error": self.last_error,
            "tickers": self.tickers,
            "last_run": datetime.utcnow().isoformat()
        }
