import logging
import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from xgboost import XGBClassifier

from core.agent_registry import register_agent

log = logging.getLogger("MLPredictorAgent")
DB_PATH = "training_data.db"

@register_agent("ml-predictor",
                description="ML model for predicting stock price direction",
                model="XGBoost Classifier",
                data_source="yfinance, indicators")
class MLPredictorAgent:
    def __init__(self):
        self.model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
        self.last_prediction_time = None
        self.ticker = "AAPL"  # Default ticker; may be updated dynamically

    def fetch_data(self, ticker="AAPL", period="30d", interval="15m"):
        df = yf.download(ticker, period=period, interval=interval)
        if df.empty:
            log.warning(f"No data returned for {ticker}")
            return None
        # Ensure the "Close" column is a one-dimensional Series.
        close_series = df["Close"].squeeze()
        df["SMA_10"] = SMAIndicator(close_series, window=10).sma_indicator()
        df["EMA_10"] = EMAIndicator(close_series, window=10).ema_indicator()
        df["RSI"] = RSIIndicator(close_series, window=14).rsi()
        df.dropna(inplace=True)
        return df

    def prepare_features(self, df):
        df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
        features = ["Close", "Volume", "SMA_10", "EMA_10", "RSI"]
        X = df[features]
        y = df["Target"]
        return train_test_split(X, y, test_size=0.2, shuffle=False)

    def train(self, X_train, y_train):
        self.model.fit(X_train, y_train)

    def predict(self, X_test):
        predictions = self.model.predict(X_test)
        probabilities = self.model.predict_proba(X_test)[:, 1]
        return predictions, probabilities

    def save_predictions(self, timestamps, predictions, confidences):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_predictions (
                timestamp TEXT,
                prediction INTEGER,
                confidence REAL,
                timeframe TEXT
            )
        """)
        now = datetime.utcnow()
        future_times = {
            "1m": now + timedelta(minutes=1),
            "5m": now + timedelta(minutes=5),
            "15m": now + timedelta(minutes=15),
            "1h": now + timedelta(hours=1),
            "3h": now + timedelta(hours=3),
            "1d": now + timedelta(days=1),
            "5d": now + timedelta(days=5),
            "10d": now + timedelta(days=10),
            "1wk": now + timedelta(weeks=1),
            "1mo": now + timedelta(days=30),
            "1yr": now + timedelta(days=365)
        }
        for tf, future_time in future_times.items():
            pred = int(predictions[-1])
            conf = float(confidences[-1])
            cursor.execute(
                "INSERT INTO ml_predictions (timestamp, prediction, confidence, timeframe) VALUES (?, ?, ?, ?)",
                (future_time.isoformat(), pred, conf, tf)
            )
        conn.commit()
        conn.close()

    def run_classification(self):
        df = self.fetch_data(ticker=self.ticker)
        if df is None or df.empty:
            log.warning("No data available for classification.")
            return
        X_train, X_test, y_train, y_test = self.prepare_features(df)
        self.train(X_train, y_train)
        y_pred, y_conf = self.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        log.info(f"[MLPredictorAgent] Classification Accuracy: {accuracy:.4f}")
        self.save_predictions(df.index[-len(y_pred):], y_pred, y_conf)

    def run(self):
        try:
            self.run_classification()
        except Exception as e:
            log.error(f"[MLPredictorAgent] Failed to run prediction: {e}")

