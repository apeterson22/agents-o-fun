import logging
import sqlite3
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import random

from core.agent_registry import register_agent

log = logging.getLogger(__name__)
DB_PATH = "databases/training_data.db"

@register_agent("crypto", description="Crypto market analysis agent", model="LLM", data_source="exchange_data, social_media")
class CryptoAgent:
    def __init__(self, symbols=None, sentiment_weight=0.5):
        """
        Initialize the CryptoAgent.
        
        Parameters:
            symbols (list): List of cryptocurrency symbols to analyze.
                            Defaults to ["BTC-USD", "ETH-USD"].
            sentiment_weight (float): Weight factor for social sentiment in confidence scoring.
        """
        self.name = "CryptoAgent"
        self.symbols = symbols if symbols is not None else ["BTC-USD", "ETH-USD"]
        self.sentiment_weight = sentiment_weight

    def fetch_crypto_data(self, symbols=None):
        """
        Fetch historical crypto data for each symbol.
        
        Returns a concatenated DataFrame with data for all symbols.
        """
        symbols = symbols if symbols is not None else self.symbols
        all_data = []
        for symbol in symbols:
            try:
                df = yf.download(symbol, period="5d", interval="30m")
                if df.empty:
                    log.warning(f"No data returned for {symbol}")
                    continue
                df["Symbol"] = symbol
                all_data.append(df)
                log.info(f"Fetched data for {symbol}")
            except Exception as e:
                log.warning(f"Failed to fetch data for {symbol}: {e}")
        return pd.concat(all_data) if all_data else pd.DataFrame()

    def fetch_social_sentiment(self, symbol):
        """
        Simulate fetching social media sentiment for a given symbol.
        In a real implementation, this would query a sentiment analysis API.
        
        Returns a sentiment score between -1 (very negative) and 1 (very positive).
        """
        try:
            sentiment = random.uniform(-1, 1)
            log.info(f"Fetched sentiment for {symbol}: {sentiment:.2f}")
            return sentiment
        except Exception as e:
            log.error(f"Error fetching sentiment for {symbol}: {e}")
            return 0
    def process_data(self, df):
        """
        Process the fetched data to compute technical indicators and integrate social sentiment.

        Computes:
          - SMA20 (20-period simple moving average)
          - EMA10 (10-period exponential moving average)
          - Return (percentage change of Close)
          - (Optionally) Adjusted confidence based on technical signal and social sentiment.
        """
        # Ensure that 'Close' is a one-dimensional Series.
        close_data = df["Close"]
        if isinstance(close_data, pd.DataFrame):
            # If there are multiple columns, choose the first one.
            if close_data.shape[1] > 1:
                close_series = close_data.iloc[:, 0]
            else:
                close_series = close_data.squeeze()
        else:
            close_series = close_data
    
        # Check that close_series is now a Series.
        if not isinstance(close_series, pd.Series):
            # As a fallback, convert to Series
            close_series = pd.Series(close_series)
####
#        # Ensure that 'Close' is a Series by squeezing it
#        close_series = df["Close"]
#        if isinstance(close_series, pd.DataFrame):
#            close_series = close_series.squeeze()  # This converts a one-column DataFrame to a Series
####
        # Compute technical indicators using the 1D Series
        df["SMA20"] = close_series.rolling(window=20).mean()
        df["EMA10"] = close_series.ewm(span=10, adjust=False).mean()
        df["Return"] = close_series.pct_change(fill_method=None)  # use the same series for percentage change

        df.dropna(inplace=True)

        predictions = []
        for index, row in df.iterrows():
            symbol = row["Symbol"]  # Assuming 'Symbol' column exists
            sentiment = self.fetch_social_sentiment(symbol)  # Your function to fetch sentiment
            base_confidence = abs(row["Return"]) * 100
            # If you wish to adjust confidence using sentiment, uncomment next line:
            # adjusted_confidence = base_confidence * (1 + self.sentiment_weight * sentiment)
            predictions.append({
                "timestamp": index.isoformat(),
                "symbol": row["Symbol"],
                "close": round(row["Close"], 4),
                "sma20": round(row["SMA20"], 4),
                "ema10": round(row["EMA10"], 4),
                "return": round(row["Return"], 6),
                "sentiment": round(sentiment, 2),
                "confidence": round(base_confidence, 2)  # or use adjusted_confidence if desired: round(adjusted_confidence, 2)
            })
        return predictions

    def save_to_db(self, records):
        """
        Save processed predictions to the database.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crypto_predictions (
                    timestamp TEXT,
                    symbol TEXT,
                    close REAL,
                    sma20 REAL,
                    ema10 REAL,
                    return REAL,
                    sentiment REAL,
                    confidence REAL
                )
            """)
            for rec in records:
                cursor.execute("""
                    INSERT INTO crypto_predictions (timestamp, symbol, close, sma20, ema10, return, sentiment, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec["timestamp"], rec["symbol"], rec["close"], rec["sma20"],
                    rec["ema10"], rec["return"], rec["sentiment"], rec["confidence"]
                ))
            conn.commit()
            conn.close()
            log.info("[CryptoAgent] Saved predictions to database.")
        except Exception as e:
            log.error(f"[CryptoAgent] Error saving to database: {e}")

    def run(self):
        """
        Execute the crypto agent's data collection, processing, and storage pipeline.
        """
        log.info("[CryptoAgent] Scanning markets and social sentiment...")
        df = self.fetch_crypto_data()
        results = self.process_data(df)
        if results:
            self.save_to_db(results)
        else:
            log.warning("[CryptoAgent] No data to process.")

