import logging
from .advanced_order_book import OrderBookModel, VolumeShareSlippageModel
from .order_manager import OrderManager

logger = logging.getLogger("ExecutionEngine")

class ExecutionEngine:
    """
    An advanced execution engine that:
      - Uses an order book model to simulate fills.
      - Applies advanced slippage models.
      - Tracks and manages multiple orders through an OrderManager.
      - Supports order cancellation.
    """
    def __init__(self, market_module, slippage_model=None):
        """
        market_module: An instance of OrderBookModel (or similar) for retrieving order book snapshots.
        slippage_model: An instance of a slippage model; if None, use default VolumeShareSlippageModel.
        """
        self.market_module = market_module
        self.slippage_model = slippage_model if slippage_model is not None else VolumeShareSlippageModel(volatility=0.02)
        self.order_manager = OrderManager()

    def submit_order(self, order):
        """
        Submit an order to the manager and simulate its execution.
        Returns the order_id.
        """
        order_id = self.order_manager.create_order(order)
        # Simulate fill using the market_module.
        fill = self.market_module.simulate_fill(order)
        if fill is None:
            logger.error("Order %s could not be filled.", order_id)
            return order_id
        extra_slippage = self.slippage_model.calculate_slippage(order.get("quantity", 1), self.market_module)
        adjusted_price = fill["weighted_avg_price"] * (1 + extra_slippage)
        fill["adjusted_price"] = adjusted_price

        # Update the order with the simulated fill.
        self.order_manager.update_order_fill(order_id, fill)
        logger.info("Order %s executed with fill: %s", order_id, fill)
        return order_id

    def cancel_order(self, order_id):
        """
        Cancel an order.
        """
        self.order_manager.cancel_order(order_id)

    def get_order_status(self, order_id):
        return self.order_manager.get_order_status(order_id)

    def get_all_orders(self):
        return self.order_manager.get_all_orders()

