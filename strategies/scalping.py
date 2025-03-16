import logging

logging.basicConfig(
    filename='logs/scalping_strategy.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def evaluate(stock_data):
    trades = []
    try:
        for symbol, data in stock_data.items():
            bid, ask = data['bid'], data['ask']
            spread = ask - bid
            if spread / bid > 0.005:
                trades.append({
                    'symbol': symbol,
                    'entry': bid,
                    'stop_loss': bid * 0.995,
                    'size': 500,
                    'order_type': 'limit',
                    'side': 'buy'
                })
                logging.info(f"Scalping opportunity identified: {symbol}")
    except Exception as e:
        logging.error(f"Error evaluating scalping trades: {e}")
    return trades

