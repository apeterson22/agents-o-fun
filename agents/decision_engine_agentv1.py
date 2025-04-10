from core.agent_registry import register_agent
import logging
import json
import sqlite3
import time
from datetime import datetime

log = logging.getLogger("DecisionEngineAgent")
DB_PATH = "databases/decision_engine.db"

@register_agent("decision-engine", description="Aggregates signals from all agents and executes trade decisions", model="Composite Decision Engine", data_source="multiple_agents")
class DecisionEngineAgent:
    def __init__(self, signal_source="agents_signals.json", trade_threshold=0.6, polling_interval=60):
        """
        Initialize the Decision Engine Agent.
        
        Parameters:
            signal_source (str): File path (or other source) for aggregated agent signals.
                                  Expected JSON structure:
                                  {
                                      "AAPL": {"signal": 0.7, "details": "MLPredictor suggests upward trend."},
                                      "BTC-USD": {"signal": -0.8, "details": "CryptoAgent shows bearish sentiment."},
                                      ...
                                  }
            trade_threshold (float): Confidence threshold to trigger a trade.
                                       Signals above this threshold prompt a 'buy',
                                       signals below the negative threshold prompt a 'sell'.
            polling_interval (int): Time in seconds between each decision cycle.
        """
        self.signal_source = signal_source
        self.trade_threshold = trade_threshold
        self.polling_interval = polling_interval
        self.status = "initialized"
        self.last_trade_time = None
        self.logger = log
        self._init_db()

    def _init_db(self):
        """Initialize the decision engine database to log trade decisions."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    asset TEXT,
                    action TEXT,
                    confidence REAL,
                    details TEXT
                )
            """)
            conn.commit()
            conn.close()
            self.logger.info("Decision Engine DB initialized.")
        except Exception as e:
            self.logger.error(f"Error initializing DB: {e}")

    def fetch_agent_signals(self):
        """
        Fetch aggregated signals from other agents.
        For simulation purposes, this function reads from a JSON file.
        Returns:
            dict: A dictionary of signals keyed by asset symbol.
        """
        try:
            with open(self.signal_source, "r") as f:
                signals = json.load(f)
            self.logger.info("Fetched agent signals successfully.")
            return signals
        except Exception as e:
            self.logger.error(f"Error fetching agent signals: {e}")
            return {}

    def decide_trade(self, signals):
        """
        Decide on trade actions based on aggregated signals.
        For each asset, if the signal exceeds the positive threshold, decide to 'buy';
        if it is below the negative threshold, decide to 'sell'; otherwise, hold.
        
        Returns:
            list: A list of trade decisions (each as a dict).
        """
        decisions = []
        for asset, info in signals.items():
            signal = info.get("signal", 0)
            details = info.get("details", "")
            action = "hold"
            if signal >= self.trade_threshold:
                action = "buy"
            elif signal <= -self.trade_threshold:
                action = "sell"
            if action != "hold":
                decision = {
                    "asset": asset,
                    "action": action,
                    "confidence": signal,
                    "details": details
                }
                decisions.append(decision)
        return decisions

    def execute_trade(self, decision):
        """
        Execute a trade decision.
        This simulation logs the trade decision and saves it to the local DB.
        In production, this method could interface with a live trading API.
        """
        timestamp = datetime.utcnow().isoformat()
        asset = decision["asset"]
        action = decision["action"]
        confidence = decision["confidence"]
        details = decision["details"]
        self.logger.info(f"Executing trade: {action.upper()} {asset} (confidence: {confidence:.2f}). Details: {details}")
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO trade_decisions (timestamp, asset, action, confidence, details) VALUES (?, ?, ?, ?, ?)",
                (timestamp, asset, action, confidence, details)
            )
            conn.commit()
            conn.close()
            self.last_trade_time = timestamp
        except Exception as e:
            self.logger.error(f"Error executing trade for {asset}: {e}")

    def run(self):
        """
        Run the decision engine continuously.
        Periodically fetch aggregated agent signals, decide on trade actions, and execute trades.
        """
        self.status = "running"
        self.logger.info("Decision Engine Agent started.")
        while self.status == "running":
            signals = self.fetch_agent_signals()
            if signals:
                decisions = self.decide_trade(signals)
                for decision in decisions:
                    self.execute_trade(decision)
            else:
                self.logger.warning("No signals received from agents.")
            time.sleep(self.polling_interval)

    def stop(self):
        """Stop the decision engine."""
        self.status = "stopped"
        self.logger.info("Decision Engine Agent stopped.")

    def health_check(self):
        """Return current health status and last trade execution time."""
        return {"status": self.status, "last_trade_time": self.last_trade_time}

