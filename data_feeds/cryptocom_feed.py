import logging
from core.crypto_interface import CryptoAPI
import pandas as pd

logging.basicConfig(
    filename='logs/cryptocom_feed.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def fetch_data(instruments, cryptocom_api_key):
    api = CryptoAPI("", cryptocom_api_key)
    data = {}
    try:
        for instrument in instruments:
            result = api.get_cryptocom_data(instrument)
            if result and 'result' in result:
                ticker_data = result['result']['data']
                df = pd.DataFrame([ticker_data])
                df['timestamp'] = pd.to_datetime(df['t'])
                df = df[['timestamp', 'a', 'b', 'c', 'h', 'l', 'v']].rename(columns={
                    'a': 'ask_price',
                    'b': 'bid_price',
                    'c': 'last_trade_price',
                    'h': 'high_price',
                    'l': 'low_price',
                    'v': 'volume'
                })
                data[instrument] = df
                logging.info(f"Fetched Crypto.com data for {instrument}")
            else:
                logging.warning(f"No data received for {instrument}")
    except Exception as e:
        logging.error(f"Error fetching Crypto.com data: {e}")
    return data
