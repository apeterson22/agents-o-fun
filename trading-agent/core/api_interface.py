import requests
import logging
import time

# Configure logging
logging.basicConfig(
    filename='logs/fidelity_api.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class FidelityAPI:
    def __init__(self, api_key, base_url="https://api.fidelity.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_market_data(self, symbol, retries=3):
        endpoint = f"{self.base_url}/marketdata/{symbol}"
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                response.raise_for_status()
                logging.info(f"Market data fetched successfully for {symbol}.")
                return response.json()
            except requests.exceptions.HTTPError as e:
                logging.error(f"HTTP error fetching market data for {symbol}: {e}")
            except requests.exceptions.ConnectionError as e:
                logging.error(f"Connection error fetching market data for {symbol}: {e}")
            except requests.exceptions.Timeout as e:
                logging.warning(f"Timeout fetching market data for {symbol}: {e}. Retrying ({attempt+1}/{retries})...")
                time.sleep(2 ** attempt)  # exponential back-off
            except requests.exceptions.RequestException as e:
                logging.critical(f"Unexpected error fetching market data for {symbol}: {e}")
                break
        return None

    def place_order(self, symbol, quantity, order_type="market", side="buy"):
        endpoint = f"{self.base_url}/orders"
        payload = {
            "symbol": symbol,
            "quantity": quantity,
            "type": order_type,
            "side": side
        }
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            logging.info(f"Order placed successfully: {side.upper()} {quantity} {symbol}.")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error placing order for {symbol}: {e}")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error placing order for {symbol}: {e}")
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout placing order for {symbol}: {e}")
        except requests.exceptions.RequestException as e:
            logging.critical(f"Unexpected error placing order for {symbol}: {e}")
        return None

