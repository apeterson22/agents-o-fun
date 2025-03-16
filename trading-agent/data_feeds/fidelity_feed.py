import logging
from core.api_interface import FidelityAPI

logging.basicConfig(
    filename='logs/fidelity_feed.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def fetch_data(symbols, api_key):
    api = FidelityAPI(api_key)
    data = {}
    try:
        for symbol in symbols:
            result = api.get_market_data(symbol)
            if result:
                data[symbol] = result
                logging.info(f"Fetched Fidelity data for {symbol}")
    except Exception as e:
        logging.error(f"Error fetching Fidelity data: {e}")
    return data

