import logging
import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator, EMAIndicator
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from xgboost import XGBClassifier, XGBRegressor

from core.agent_registry import register_agent

log = logging.getLogger("MLPredictorAgent")
DB_PATH = "training_data.db"

@register_agent("ml-predictor", description="ML model for predicting stock price direction",
                model="XGBoost Model", data_source="yfinance, indicators")
class MLPredictorAgent:
    def __init__(self, mode="classification", ticker="AAPL"):
        """
        Initialize the ML Predictor Agent.
        
        Parameters:
            mode (str): Prediction mode; either "classification" for short-term directional prediction
                        or "regression" for long-term price forecasting.
            ticker (str): Stock ticker symbol to analyze.
        """
        self.mode = mode
        self.ticker = ticker
        self.last_prediction_time = None
        
        if mode == "classification":
            self.model = XGBClassifier(use_label_encoder=False, eval_metric="logloss")
        elif mode == "regression":
            self.model = XGBRegressor(objective="reg:squarederror", n_estimators=100)
        else:
            raise ValueError("Unsupported mode. Choose 'classification' or 'regression'.")

    # ---------------------------
    # Classification Pipeline
    # ---------------------------
    def fetch_data(self, ticker=None, period="30d", interval="15m"):
        """
        Fetch historical stock data and compute technical indicators for classification.
        """
        ticker = ticker or self.ticker
        df = yf.download(ticker, period=period, interval=interval)
        if df.empty:
            log.warning(f"No data returned for {ticker}")
            return None
        # Compute technical indicators
        df["SMA_10"] = SMAIndicator(df["Close"], window=10).sma_indicator()
        df["EMA_10"] = EMAIndicator(df["Close"], window=10).ema_indicator()
        df["RSI"] = RSIIndicator(df["Close"], window=14).rsi()
        df.dropna(inplace=True)
        return df

    def prepare_features(self, df):
        """
        Prepare features for classification.
        Target: 1 if the next closing price is higher than the current closing price; 0 otherwise.
        """
        df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)
        features = ["Close", "Volume", "SMA_10", "EMA_10", "RSI"]
        X = df[features]
        y = df["Target"]
        return train_test_split(X, y, test_size=0.2, shuffle=False)

    def train(self, X_train, y_train):
        """Train the classification model."""
        self.model.fit(X_train, y_train)

    def predict(self, X_test):
        """Predict using the classification model."""
        preds = self.model.predict(X_test)
        probs = self.model.predict_proba(X_test)[:, 1]
        return preds, probs

    def save_predictions(self, timestamps, predictions, confidences):
        """
        Save classification predictions into the database with multiple future time horizons.
        """
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
        # For demonstration, save the last prediction for each horizon.
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
        """
        Execute the full classification pipeline.
        """
        df = self.fetch_data(ticker=self.ticker)
        if df is None or df.empty:
            log.warning("[MLPredictorAgent] No data fetched for classification.")
            return
        X_train, X_test, y_train, y_test = self.prepare_features(df)
        self.train(X_train, y_train)
        y_pred, y_conf = self.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        log.info(f"[MLPredictorAgent] Classification Accuracy: {acc:.4f}")
        self.save_predictions(df.index[-len(y_pred):], y_pred, y_conf)
        self.last_prediction_time = datetime.utcnow()

    # ---------------------------
    # Regression Pipeline
    # ---------------------------
    def _get_data(self, ticker=None, period="60d", interval="5m"):
        """
        Fetch historical stock data and compute technical indicators for regression.
        """
        ticker = ticker or self.ticker
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        df.dropna(inplace=True)
        df["SMA_20"] = df["Close"].rolling(window=20).mean()
        df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["Momentum"] = df["Close"] - df["Close"].shift(5)
        df.dropna(inplace=True)
        return df

    def _prepare_dataset(self, df):
        """
        Prepare features for regression.
        Target: Next closing price.
        """
        features = ["Open", "High", "Low", "Close", "Volume", "SMA_20", "EMA_20", "Momentum"]
        df["Target"] = df["Close"].shift(-1)
        df.dropna(inplace=True)
        X = df[features]
        y = df["Target"]
        return train_test_split(X, y, test_size=0.2, shuffle=False)

    def _train_model(self, X_train, y_train):
        """Train a regression model."""
        model = XGBRegressor(objective="reg:squarederror", n_estimators=100)
        model.fit(X_train, y_train)
        return model

    def _evaluate_and_log(self, model, X_test, y_test, predictions, ticker):
        """
        Evaluate the regression model and log performance metrics.
        """
        mse = mean_squared_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)
        timestamp = datetime.now().isoformat()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ml_regression_metrics (
                timestamp TEXT,
                ticker TEXT,
                mse REAL,
                r2 REAL
            )
        """)
        cursor.execute("INSERT INTO ml_regression_metrics (timestamp, ticker, mse, r2) VALUES (?, ?, ?, ?)",
                       (timestamp, ticker, mse, r2))
        conn.commit()
        conn.close()
        log.info(f"[MLPredictorAgent] Regression for {ticker} | MSE: {mse:.4f}, R2: {r2:.4f}")

    def run_regression(self):
        """
        Execute the full regression pipeline.
        """
        df = self._get_data(ticker=self.ticker)
        if df is None or df.empty:
            log.warning("[MLPredictorAgent] No data fetched for regression.")
            return
        X_train, X_test, y_train, y_test = self._prepare_dataset(df)
        reg_model = self._train_model(X_train, y_train)
        predictions = reg_model.predict(X_test)
        self._evaluate_and_log(reg_model, X_test, y_test, predictions, self.ticker)
        self.last_prediction_time = datetime.utcnow()

    # ---------------------------
    # Unified Run Method
    # ---------------------------
    def run(self):
        """
        Execute the prediction pipeline based on the selected mode.
        """
        try:
            if self.mode == "classification":
                self.run_classification()
            elif self.mode == "regression":
                self.run_regression()
            else:
                log.error(f"[MLPredictorAgent] Unknown mode: {self.mode}")
        except Exception as e:
            log.error(f"[MLPredictorAgent] Failed to run prediction: {e}")

