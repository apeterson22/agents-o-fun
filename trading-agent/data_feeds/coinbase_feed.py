import logging
from core.crypto_interface import CryptoAPI

logging.basicConfig(
    filename='logs/coinbase_feed.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def fetch_data(symbols, coinbase_api_key):
    api = CryptoAPI(coinbase_api_key, "")
    data = {}
    try:
        for symbol in symbols:
            result = api.get_coinbase_data(symbol)
            if result:
                data[symbol] = result
                logging.info(f"Fetched Coinbase data for {symbol}")
    except Exception as e:
        logging.error(f"Error fetching Coinbase data: {e}")
    return data

