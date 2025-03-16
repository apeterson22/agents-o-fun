import logging

logging.basicConfig(
    filename='logs/momentum_strategy.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def evaluate(stock_data):
    trades = []
    try:
        for symbol, data in stock_data.items():
            price_history = data['prices'][-10:]
            if price_history[-1] > price_history[0] * 1.05:
                trades.append({
                    'symbol': symbol,
                    'entry': price_history[-1],
                    'stop_loss': price_history[-1] * 0.97,
                    'size': 1000,
                    'order_type': 'market',
                    'side': 'buy'
                })
                logging.info(f"Momentum trade identified: {symbol}")
    except Exception as e:
        logging.error(f"Error evaluating momentum trades: {e}")
    return trades

