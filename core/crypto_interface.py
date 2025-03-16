import requests
import logging
import time

# Configure logging
logging.basicConfig(
    filename='logs/crypto_api.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class CryptoAPI:
    def __init__(self, coinbase_api_key, cryptocom_api_key):
        self.coinbase_api_key = coinbase_api_key
        self.cryptocom_api_key = cryptocom_api_key
        self.coinbase_base_url = "https://api.coinbase.com/v2"
        self.cryptocom_base_url = "https://api.crypto.com/v2"

    # Coinbase market data fetcher
    def get_coinbase_data(self, symbol, retries=3):
        endpoint = f"{self.coinbase_base_url}/prices/{symbol}/spot"
        headers = {"Authorization": f"Bearer {self.coinbase_api_key}"}
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                response.raise_for_status()
                logging.info(f"Coinbase market data fetched successfully for {symbol}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Coinbase error for {symbol}: {e}. Retry {attempt+1}/{retries}")
                time.sleep(2 ** attempt)
        return None

    # Crypto.com market data fetcher
    def get_cryptocom_data(self, instrument_name, retries=3):
        endpoint = f"{self.cryptocom_base_url}/public/get-ticker?instrument_name={instrument_name}"
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, timeout=10)
                response.raise_for_status()
                logging.info(f"Crypto.com market data fetched successfully for {instrument_name}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Crypto.com error for {instrument_name}: {e}. Retry {attempt+1}/{retries}")
                time.sleep(2 ** attempt)
        return None

    # Coinbase order placement
    def place_coinbase_order(self, symbol, amount, side="buy", retries=2):
        endpoint = f"{self.coinbase_base_url}/accounts/orders"
        payload = {
            "symbol": symbol,
            "amount": amount,
            "side": side
        }
        headers = {"Authorization": f"Bearer {self.coinbase_api_key}"}
        for attempt in range(retries):
            try:
                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                logging.info(f"Coinbase order placed: {side.upper()} {amount} {symbol}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Coinbase order error for {symbol}: {e}. Retry {attempt+1}/{retries}")
                time.sleep(2 ** attempt)
        return None

    # Crypto.com order placement
    def place_cryptocom_order(self, instrument_name, quantity, side="BUY", retries=2):
        endpoint = f"{self.cryptocom_base_url}/private/create-order"
        payload = {
            "instrument_name": instrument_name,
            "quantity": quantity,
            "side": side,
            "type": "MARKET"
        }
        headers = {"Authorization": f"Bearer {self.cryptocom_api_key}"}
        for attempt in range(retries):
            try:
                response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
                response.raise_for_status()
                logging.info(f"Crypto.com order placed: {side.upper()} {quantity} {instrument_name}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Crypto.com order error for {instrument_name}: {e}. Retry {attempt+1}/{retries}")
                time.sleep(2 ** attempt)
        return None

