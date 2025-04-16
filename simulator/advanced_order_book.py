import logging
import random
import numpy as np
import pandas as pd

# Configure logging for the advanced order book module.
logging.basicConfig(
    filename='logs/advanced_order_book.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)
logger = logging.getLogger("AdvancedOrderBook")


class OrderBookModel:
    """
    Models an order book for a market, including bid and ask levels.
    
    Attributes:
        bids (list of tuples): Each tuple is (price, available_volume) for bids, sorted descending.
        asks (list of tuples): Each tuple is (price, available_volume) for asks, sorted ascending.
        timestamp (datetime): Timestamp for the snapshot.
    """
    def __init__(self, bids=None, asks=None, timestamp=None):
        # For a real system, bids and asks would be loaded from live/historical order book data.
        # Here, we allow them to be passed in (or generate a dummy order book).
        self.bids = bids if bids is not None else self._generate_dummy_bids()
        self.asks = asks if asks is not None else self._generate_dummy_asks()
        self.timestamp = timestamp

    def _generate_dummy_bids(self):
        # Generate dummy bid levels (price descending)
        base_price = 100
        return [(base_price - i * 0.05, random.randint(100, 500)) for i in range(5)]

    def _generate_dummy_asks(self):
        # Generate dummy ask levels (price ascending)
        base_price = 100
        return [(base_price + i * 0.05, random.randint(100, 500)) for i in range(5)]

    def simulate_fill(self, order):
        """
        Simulate an order fill using the current order book.
        
        Parameters:
            order (dict): Must include:
                - 'side': 'buy' or 'sell'
                - 'quantity': desired quantity to trade
                
        Returns:
            dict: Details of the fill, including the weighted average fill price,
                  total filled volume, and any partial fill information.
        """
        side = order.get("side", "").lower()
        quantity = order.get("quantity", 0)
        filled = 0
        total_cost = 0
        fill_levels = []

        if side == "buy":
            levels = self.asks
        elif side == "sell":
            levels = self.bids
        else:
            logger.error("simulate_fill: Invalid order side: %s", side)
            return None

        for price, available in levels:
            if filled >= quantity:
                break
            fill_qty = min(quantity - filled, available)
            filled += fill_qty
            cost = price * fill_qty
            total_cost += cost
            fill_levels.append({"price": price, "quantity": fill_qty})
            # Simulate that the available volume is consumed (for the simulation)
        
        if filled == 0:
            logger.warning("simulate_fill: Order could not be filled at any level.")
            return None

        weighted_avg_price = total_cost / filled
        result = {
            "filled_quantity": filled,
            "weighted_avg_price": weighted_avg_price,
            "fill_levels": fill_levels
        }
        logger.info("Order fill result: %s", result)
        return result


class VolumeShareSlippageModel:
    """
    Models slippage dynamically based on the order size as a fraction of order book volume
    and market volatility.
    """
    def __init__(self, volatility=0.02):
        """
        Parameters:
            volatility (float): A measure of market volatility (default 2%).
        """
        self.volatility = volatility

    def calculate_slippage(self, order_quantity, order_book: OrderBookModel):
        """
        Calculate an additional slippage percentage based on the order's size relative
        to the total available volume in the order book.
        
        Parameters:
            order_quantity (float): The quantity of the order.
            order_book (OrderBookModel): The current order book snapshot.
            
        Returns:
            float: Additional slippage percentage (e.g. 0.005 for 0.5% extra cost).
        """
        # Calculate total available volume (summing asks for buy orders, bids for sell)
        total_volume = 0
        for level in (order_book.asks + order_book.bids):
            total_volume += level[1]

        if total_volume == 0:
            return 0

        volume_ratio = order_quantity / total_volume
        # A simple linear model: slippage increases with volume ratio, scaled by volatility.
        additional_slippage = self.volatility * volume_ratio
        logger.info("Calculated additional slippage: %.4f for order ratio: %.4f", additional_slippage, volume_ratio)
        return additional_slippage


class AlternativeDataIntegrator:
    """
    A stub for integrating alternative data.
    In a real system, this class would connect to news APIs, economic databases, or social media streams.
    """
    def __init__(self):
        pass

    def get_sentiment(self, asset):
        """
        Retrieve a sentiment score for the asset.
        Returns a score between -1 and 1.
        For demo purposes, this randomly returns a value.
        """
        sentiment_score = random.uniform(-1, 1)
        logger.info("AlternativeDataIntegrator: Sentiment for %s: %.2f", asset, sentiment_score)
        return sentiment_score

    def get_macro_indicators(self):
        """
        Retrieve macroeconomic indicators.
        Returns a dictionary with dummy values.
        """
        indicators = {
            "GDP_growth": random.uniform(1, 3),
            "inflation": random.uniform(1, 2),
            "interest_rate": random.uniform(0, 5)
        }
        logger.info("Retrieved macroeconomic indicators: %s", indicators)
        return indicators


# Example usage integrated into the order execution process:
if __name__ == "__main__":
    # Create a dummy order book with randomly generated levels.
    order_book = OrderBookModel()
    # Create a volume-share slippage model with default volatility.
    slippage_model = VolumeShareSlippageModel()
    # Create an alternative data integrator for sentiment, etc.
    alt_data = AlternativeDataIntegrator()

    # Simulate a sample order:
    sample_order = {
        "side": "buy",
        "quantity": 1000
    }
    # Simulate order fill from the order book.
    fill = order_book.simulate_fill(sample_order)
    if fill:
        # Calculate additional slippage:
        extra_slippage = slippage_model.calculate_slippage(sample_order["quantity"], order_book)
        # Adjust fill price for slippage:
        adjusted_fill_price = fill["weighted_avg_price"] * (1 + extra_slippage)
        logger.info("Adjusted fill price after slippage: %.4f", adjusted_fill_price)
    
    # Get sentiment for a sample asset:
    sentiment = alt_data.get_sentiment("AAPL")
    logger.info("Sample sentiment for AAPL: %.2f", sentiment)
    
    # Get macro indicators:
    indicators = alt_data.get_macro_indicators()
    logger.info("Macroeconomic indicators: %s", indicators)

