import os
import sys
import logging
import random
import numpy as np
import pandas as pd
import datetime
import time

# Ensure project root is in sys.path (if needed).
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..")
if project_root not in sys.path:
    sys.path.append(project_root)

# Use relative imports for modules in this package.
from .realtime_data_feed import RealTimeDataFeed
from .execution_engine import ExecutionEngine
from .advanced_order_book import OrderBookModel  # For fallback
from .order_manager import OrderManager
from configs.config_loader import load_config

logger = logging.getLogger("AdvancedTradingSimulator")
logging.basicConfig(
    filename='logs/advanced_trading_simulator.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

# --- Dynamic Asset Selection Helpers ---
def select_top_movers(df, n=1):
    grouped = df.groupby("Symbol")
    returns = grouped["close"].agg(lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0])
    top_symbols = returns.sort_values(ascending=False).head(n).index.tolist()
    logger.info("Top movers: %s", top_symbols)
    return top_symbols

def select_bottom_movers(df, n=1):
    grouped = df.groupby("Symbol")
    returns = grouped["close"].agg(lambda x: (x.iloc[-1] - x.iloc[0]) / x.iloc[0])
    bottom_symbols = returns.sort_values(ascending=True).head(n).index.tolist()
    logger.info("Bottom movers: %s", bottom_symbols)
    return bottom_symbols


class AdvancedTradingSimulator:
    def __init__(self, mode="backtest", feed_mode="simulated", start_date=None, end_date=None, timeframe="5min"):
        """
        mode: "backtest" for one-cycle simulation or "live" for continuous paper trading.
        feed_mode: "simulated" uses synthetic data; "real" uses real-world data via providers.
        """
        self.mode = mode
        self.feed_mode = feed_mode
        self.start_date = pd.to_datetime(start_date) if start_date else pd.to_datetime(datetime.datetime.now() - datetime.timedelta(days=30))
        self.end_date = pd.to_datetime(end_date) if end_date else pd.to_datetime(datetime.datetime.now())
        self.timeframe = timeframe
        self.performance_log = []
        
        # Load configuration for data feeds from the YAML config.
        self.config = load_config()
        # Real-time data feed instance.
        if self.feed_mode == "real":
            self.data_feed = RealTimeDataFeed(self.config)
            # Let the configuration specify a universe dynamically.
            self.universe = self.config.get("universe", ["AAPL", "GOOGL", "MSFT", "TSLA", "BTC-USD", "EURUSD", "NFLX"])
        else:
            self.historical_data = self._generate_synthetic_data()

        # Set up the execution engine using a simulated order book as fallback.
        self.execution_engine = ExecutionEngine(market_module=OrderBookModel())

    def _generate_synthetic_data(self):
        symbols = ["AAPL", "GOOGL", "BTC-USD", "EURUSD", "NFLX", "TSLA", "AMD"]
        date_range = pd.date_range(start=self.start_date, end=self.end_date, freq=self.timeframe)
        records = []
        for symbol in symbols:
            base_price = random.uniform(50, 250)
            prices = [base_price]
            for _ in range(1, len(date_range)):
                drift = 0.0001
                shock = random.gauss(0, 0.001)
                new_price = prices[-1] * np.exp(drift + shock)
                prices.append(new_price)
            df_symbol = pd.DataFrame({
                "timestamp": date_range,
                "Symbol": symbol,
                "close": prices
            })
            records.append(df_symbol)
        df_all = pd.concat(records, ignore_index=True)
        logger.info("Generated synthetic data for assets: %s", symbols)
        return df_all

    def load_data(self, symbol):
        """
        Load data for a given symbol using real or simulated mode.
        """
        if self.feed_mode == "real":
            # For equities, use yfinance.
            # For crypto or forex, determine based on symbol.
            if "-" in symbol:
                if symbol.endswith("USD"):
                    # Try crypto first.
                    df = self.data_feed.load_data_crypto(symbol, self.start_date, self.end_date, self.timeframe)
                    if df.empty:
                        # Optionally, treat as forex if appropriate.
                        df = self.data_feed.load_data_forex(symbol[:3], symbol[-3:], self.start_date, self.end_date, self.timeframe)
                else:
                    df = self.data_feed.load_data_crypto(symbol, self.start_date, self.end_date, self.timeframe)
            else:
                df = self.data_feed.load_data_equities(symbol, self.start_date, self.end_date, self.timeframe)
            return df
        else:
            return self.historical_data[self.historical_data["Symbol"] == symbol]

    def select_assets_for_trading(self):
        """
        Dynamically select assets from the universe based on performance.
        """
        if self.feed_mode == "simulated":
            df = self.historical_data
        else:
            data_list = []
            for symbol in self.universe:
                df_symbol = self.load_data(symbol)
                if not df_symbol.empty:
                    data_list.append(df_symbol)
            if not data_list:
                logger.error("No data loaded from the real data feed for the universe.")
                return []
            df = pd.concat(data_list)
        top = select_top_movers(df, n=1)
        bottom = select_bottom_movers(df, n=1)
        selected = list(set(top + bottom))
        logger.info("Dynamically selected assets: %s", selected)
        return selected

    def simulate_order_execution(self, order, symbol):
        """
        Execute the order using the advanced execution engine.
        """
        execution = self.execution_engine.submit_order(order)
        return execution

    def run_simulation_cycle(self):
        """
        Run one simulation cycle:
          - Dynamically select assets.
          - For each asset, load its data.
          - Generate a dummy order (this can be replaced with a real strategy).
          - Execute the order via the execution engine.
        """
        results = []
        selected_assets = self.select_assets_for_trading()
        if not selected_assets:
            logger.warning("No assets selected for trading.")
            return results
        for symbol in selected_assets:
            df = self.load_data(symbol)
            if df.empty:
                continue
            if random.random() < 0.5:
                current_price = df.iloc[-1]["close"]
                order = {
                    "side": random.choice(["buy", "sell"]),
                    "quantity": random.randint(1, 100),
                    "entry": current_price,
                    "stop_loss": current_price * 0.97
                }
                execution = self.simulate_order_execution(order, symbol)
                result = {
                    "symbol": symbol,
                    "order": order,
                    "execution": execution,
                    "timestamp": datetime.datetime.now().isoformat()
                }
                results.append(result)
                logger.info("Simulated trade for %s: %s", symbol, result)
        self.performance_log.extend(results)
        return results

    def run(self):
        """
        Run the simulator in backtest (single cycle) or live mode.
        """
        if self.mode == "backtest":
            logger.info("Running simulator in backtest mode.")
            results = self.run_simulation_cycle()
            logger.info("Backtest complete with %d trades.", len(results))
            return results
        elif self.mode == "live":
            logger.info("Running simulator in live mode.")
            while True:
                results = self.run_simulation_cycle()
                logger.info("Live cycle complete with %d trades.", len(results))
                time.sleep(60)
        else:
            raise ValueError("Invalid mode. Use 'backtest' or 'live'.")


if __name__ == "__main__":
    # For testing, we can load configuration from YAML.
    from configs.config_loader import load_config
    config = load_config()
    # Optionally update the data feed configuration using the dashboard interface later.
    simulator = AdvancedTradingSimulator(
        mode="backtest",
        feed_mode="real",  # Use "real" for live data feeds or "simulated" for synthetic data.
        start_date="2025-03-01",
        end_date="2025-03-31",
        timeframe="5min"
    )
    sim_results = simulator.run()
    print("Simulation complete with", len(sim_results), "trades executed.")
    for res in sim_results:
        print(res)

