import pandas as pd
import numpy as np
import datetime
import logging
import time
import random

import os
import sys

# Add the project root directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..")
if project_root not in sys.path:
    sys.path.append(project_root)

logging.basicConfig(
    filename='logs/trading_simulator.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)
logger = logging.getLogger("TradingSimulator")

# Assume these modules exist from your project:
from core.risk_manager import RiskManager
from core.regulatory_compliance import RegulatoryCompliance
# For live data simulation, you might use a data provider interface already built,
# or use a file-based historical data loader for backtesting.
# Here, we simulate with random data if needed.

# --- Market Module Base Class ---
class MarketModule:
    """
    Base class for a market module.
    Each module is responsible for:
      - Loading historical data (for backtesting) or connecting to live data feeds.
      - Simulating order execution (applying execution costs such as spreads, slippage, commissions)
      - Providing market-specific metadata (e.g., trading hours, asset multipliers, etc.)
    """
    def __init__(self, name, commission_rate=0.001, spread=0.01, slippage_pct=0.001):
        self.name = name
        self.commission_rate = commission_rate  # as a fraction of trade value
        self.spread = spread                    # spread in absolute or relative terms
        self.slippage_pct = slippage_pct        # proportion of price to adjust for slippage

    def load_data(self, start_date, end_date, timeframe):
        """
        Load historical data for backtesting.
        Returns a pandas DataFrame with columns such as timestamp, open, high, low, close, volume.
        (You can extend this method to load from CSV, database, or external API.)
        """
        # Dummy implementation: generate random price data.
        date_range = pd.date_range(start=start_date, end=end_date, freq=timeframe)
        data = {
            "timestamp": date_range,
            "open": np.random.uniform(100, 200, len(date_range)),
            "high": np.random.uniform(200, 300, len(date_range)),
            "low": np.random.uniform(50, 100, len(date_range)),
            "close": np.random.uniform(100, 200, len(date_range)),
            "volume": np.random.randint(1000, 5000, len(date_range))
        }
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        logger.info("MarketModule [%s]: Loaded %d bars of historical data.", self.name, len(df))
        return df

    def simulate_order_execution(self, order, current_price):
        """
        Simulate order execution by applying execution costs.
        
        order: dict with keys: 'side' (buy/sell), 'quantity'
        current_price: the current market price
        
        Returns:
            dict: Execution details (filled_price, commission, slippage, net_price)
        """
        # Apply spread:
        if order["side"] == "buy":
            fill_price = current_price * (1 + self.spread/2)
        else:
            fill_price = current_price * (1 - self.spread/2)
        
        # Apply slippage:
        fill_price *= (1 + self.slippage_pct * (random.random() - 0.5))  # random deviation

        # Compute commission:
        commission = order["quantity"] * fill_price * self.commission_rate

        net_price = fill_price + commission if order["side"] == "buy" else fill_price - commission

        execution = {
            "filled_price": fill_price,
            "commission": commission,
            "net_price": net_price
        }
        return execution


# --- Example Market Modules ---
class EquitiesModule(MarketModule):
    def __init__(self, **kwargs):
        super().__init__(name="Equities", **kwargs)
        # Additional equities-specific settings can be included here.


class CryptoModule(MarketModule):
    def __init__(self, **kwargs):
        super().__init__(name="Crypto", **kwargs)
        # You might have lower commissions but higher slippage.


class ForexModule(MarketModule):
    def __init__(self, **kwargs):
        super().__init__(name="Forex", **kwargs)
        # Forex may trade 24/5; spreads might be variable.


class OptionsModule(MarketModule):
    def __init__(self, **kwargs):
        super().__init__(name="Options", **kwargs)
        # Options require handling multiple contracts, expiries, and Greeks.


class SportsModule(MarketModule):
    def __init__(self, **kwargs):
        super().__init__(name="Sports", **kwargs)
        # Sports betting might simulate odds changes and commission per bet.


# --- Execution Engine ---
class ExecutionEngine:
    def __init__(self, market_modules):
        """
        Initialize the execution engine with available market modules.
        
        market_modules: dict mapping market names (e.g., 'Equities', 'Crypto') to module instances.
        """
        self.market_modules = market_modules

    def execute_order(self, market_name, order, current_price):
        """
        Route the order to the appropriate market module for execution.
        """
        module = self.market_modules.get(market_name)
        if module:
            execution_details = module.simulate_order_execution(order, current_price)
            logger.info("Executed order on %s: %s", market_name, execution_details)
            return execution_details
        else:
            logger.error("No market module found for %s", market_name)
            return None


# --- Trading Simulator ---
class TradingSimulator:
    def __init__(self, mode="backtest", start_date=None, end_date=None, timeframe="5min"):
        """
        Initialize the simulator.
        
        mode: "backtest" or "live" (paper trading)
        start_date, end_date: for backtesting
        timeframe: resolution (e.g., "1min", "5min", "1H", "1D", "1W")
        """
        self.mode = mode
        self.start_date = start_date or (datetime.datetime.now() - datetime.timedelta(days=30))
        self.end_date = end_date or datetime.datetime.now()
        self.timeframe = timeframe
        self.performance_log = []
        
        # Instantiate market modules for each market type.
        self.market_modules = {
            "Equities": EquitiesModule(commission_rate=0.001, spread=0.01, slippage_pct=0.001),
            "Crypto": CryptoModule(commission_rate=0.001, spread=0.005, slippage_pct=0.002),
            "Forex": ForexModule(commission_rate=0.0005, spread=0.0001, slippage_pct=0.0005),
            "Options": OptionsModule(commission_rate=0.005, spread=0.05, slippage_pct=0.01),
            "Sports": SportsModule(commission_rate=0.02, spread=0.02, slippage_pct=0.0)
        }
        self.execution_engine = ExecutionEngine(self.market_modules)

        # Instantiate Risk and Regulatory managers – using your existing modules:
        self.risk_manager = RiskManager(max_daily_loss=5000, stop_loss_pct=0.03, max_position_size=2000, daily_goal=10000)
        self.regulatory = RegulatoryCompliance(trading_start=9, trading_end=16, max_trades_per_day=100)

    def backtest(self, strategy):
        """
        Run a backtest of the strategy across multiple markets.
        """
        logger.info("Starting backtest mode with timeframe: %s", self.timeframe)
        results = []
        for market_name, module in self.market_modules.items():
            # Load historical data for this market.
            df = module.load_data(self.start_date, self.end_date, self.timeframe)
            # Send the data to the strategy for generating orders.
            # Here, we assume that the strategy has a method `generate_orders(market, data)`
            orders = strategy.generate_orders(market_name, df)
            logger.info("Market %s: Strategy generated %d orders.", market_name, len(orders))
            # Simulate execution for each order:
            for order in orders:
                # Assume we use the 'close' price of the relevant row (or some dummy current price)
                current_price = df.iloc[-1]["close"] if not df.empty else 100
                # Check risk & regulatory compliance
                if not self.regulatory.check_compliance():
                    logger.warning("Trade skipped due to compliance limits.")
                    continue
                if not self.risk_manager.assess_trade_risk(order.get("entry", current_price), order.get("stop_loss", current_price * 0.97), order.get("quantity", 1)):
                    logger.warning("Trade rejected by risk limits: %s", order)
                    continue
                execution = self.execution_engine.execute_order(market_name, order, current_price)
                results.append({
                    "market": market_name,
                    "order": order,
                    "execution": execution,
                    "timestamp": datetime.datetime.now().isoformat()
                })
        # Log performance summary
        self.performance_log = results
        logger.info("Backtest complete. Executed %d trades.", len(results))
        return results

    def paper_trade(self, strategy):
        """
        Run live paper trading using the same strategy.
        This method will subscribe to live data feeds (or simulate live data)
        and execute orders in real-time.
        """
        logger.info("Starting live paper trading mode with timeframe: %s", self.timeframe)
        # For a simplified simulation, we use the same data loader as backtest.
        while True:
            for market_name, module in self.market_modules.items():
                df = module.load_data(self.start_date, self.end_date, self.timeframe)  # In live, replace with real-time feed.
                orders = strategy.generate_orders(market_name, df)
                for order in orders:
                    current_price = df.iloc[-1]["close"] if not df.empty else 100
                    if not self.regulatory.check_compliance():
                        logger.warning("Live trade skipped due to compliance limits.")
                        continue
                    if not self.risk_manager.assess_trade_risk(order.get("entry", current_price), order.get("stop_loss", current_price * 0.97), order.get("quantity", 1)):
                        logger.warning("Live trade rejected by risk limits: %s", order)
                        continue
                    execution = self.execution_engine.execute_order(market_name, order, current_price)
                    self.performance_log.append({
                        "market": market_name,
                        "order": order,
                        "execution": execution,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    # Update risk manager with simulated profit or loss
                    profit = execution["net_price"] - order.get("entry", current_price)
                    if profit >= 0:
                        self.risk_manager.update_daily_profit(profit)
                    else:
                        self.risk_manager.update_daily_loss(abs(profit))
            # Sleep for a period matching the timeframe or live update frequency.
            time.sleep(60)

    def run(self, strategy):
        """
        High-level run method to choose between backtest and paper trading.
        """
        if self.mode == "backtest":
            return self.backtest(strategy)
        elif self.mode == "live":
            return self.paper_trade(strategy)
        else:
            raise ValueError("Invalid mode. Choose 'backtest' or 'live'.")

# --- Example Strategy Implementation ---
class DummyStrategy:
    """
    A dummy strategy for demonstration purposes.
    It randomly decides to generate a trade order based on a probability.
    """
    def generate_orders(self, market_name, df):
        orders = []
        if df.empty:
            return orders
        # For demonstration, randomly generate an order 50% of the time
        if random.random() < 0.5:
            # Use last observed price as the basis
            price = df.iloc[-1]["close"]
            order = {
                "side": random.choice(["buy", "sell"]),
                "quantity": random.randint(1, 10),
                "entry": price,
                "stop_loss": price * 0.97  # example stop loss at 3% below entry for long
            }
            orders.append(order)
        return orders

# --- Example Usage ---
if __name__ == "__main__":
    # Create a dummy strategy for testing.
    strategy = DummyStrategy()
    # Create a TradingSimulator instance in backtest mode.
    simulator = TradingSimulator(
        mode="backtest",
        start_date="2025-03-01",
        end_date="2025-03-31",
        timeframe="5min"
    )
    results = simulator.run(strategy)
    print("Backtest completed with", len(results), "trades executed.")
