import logging

logging.basicConfig(
    filename='logs/crypto_strategy.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def evaluate(crypto_data):
    trades = []
    try:
        for symbol, data in crypto_data.items():
            price_change = data['24h_change']
            if price_change > 5:
                trades.append({
                    'symbol': symbol,
                    'entry': data['current_price'],
                    'stop_loss': data['current_price'] * 0.95,
                    'size': 2,
                    'order_type': 'market',
                    'side': 'buy'
                })
                logging.info(f"Crypto trade identified: {symbol}")
    except Exception as e:
        logging.error(f"Error evaluating crypto trades: {e}")
    return trades

