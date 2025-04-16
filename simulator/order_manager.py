import uuid
import logging

logger = logging.getLogger("OrderManager")

class OrderManager:
    """
    A simple order management system to track multiple orders,
    handle partial fills, and process cancellations.
    """
    def __init__(self):
        # Orders are stored as dict: order_id -> order details.
        self.orders = {}

    def generate_order_id(self):
        return str(uuid.uuid4())

    def create_order(self, order):
        """
        Create a new order and assign a unique order id.
        """
        order_id = self.generate_order_id()
        order_record = {
            "order_id": order_id,
            "order": order,
            "filled_quantity": 0,
            "status": "open",  # possible statuses: open, partially_filled, filled, cancelled
            "execution_details": []
        }
        self.orders[order_id] = order_record
        logger.info("Created new order: %s", order_record)
        return order_id

    def update_order_fill(self, order_id, fill):
        """
        Update an order with a new fill.
        """
        if order_id not in self.orders:
            logger.error("Order %s not found for update.", order_id)
            return
        order_record = self.orders[order_id]
        order_record["execution_details"].append(fill)
        order_record["filled_quantity"] += fill.get("filled_quantity", 0)
        total_qty = order_record["order"].get("quantity", 0)
        if order_record["filled_quantity"] >= total_qty:
            order_record["status"] = "filled"
        else:
            order_record["status"] = "partially_filled"
        logger.info("Updated order %s with fill: %s", order_id, fill)

    def cancel_order(self, order_id):
        """
        Cancel an order.
        """
        if order_id in self.orders:
            self.orders[order_id]["status"] = "cancelled"
            logger.info("Cancelled order %s.", order_id)
        else:
            logger.warning("Attempt to cancel non-existent order %s.", order_id)

    def get_order_status(self, order_id):
        """
        Retrieve the status of an order.
        """
        return self.orders.get(order_id, {}).get("status", "not_found")

    def get_all_orders(self):
        """
        Return all orders.
        """
        return self.orders

