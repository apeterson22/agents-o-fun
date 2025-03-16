import logging

logging.basicConfig(
    filename='logs/arbitrage_strategy.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def evaluate(stock_data):
    trades = []
    try:
        for symbol, data in stock_data.items():
            prices = data['prices']
            if max(prices) - min(prices) > 0.02 * min(prices):
                trades.append({
                    'symbol': symbol,
                    'entry': min(prices),
                    'stop_loss': min(prices) * 0.98,
                    'size': 1000,
                    'order_type': 'market',
                    'side': 'buy'
                })
                logging.info(f"Arbitrage opportunity identified: {symbol}")
    except Exception as e:
        logging.error(f"Error evaluating arbitrage trades: {e}")
    return trades

