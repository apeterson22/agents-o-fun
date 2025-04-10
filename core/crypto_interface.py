import requests
import logging
import time

logging.basicConfig(
    filename='logs/crypto_api.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class CryptoAPI:
    def __init__(self, coinbase_api_key, cryptocom_api_key, max_retries=3, timeout=10):
        """
        Initialize the CryptoAPI interface.
        
        Parameters:
            coinbase_api_key (str): API key for Coinbase.
            cryptocom_api_key (str): API key for Crypto.com.
            max_retries (int): Maximum number of retries for each request.
            timeout (int): Request timeout in seconds.
        """
        self.coinbase_api_key = coinbase_api_key
        self.cryptocom_api_key = cryptocom_api_key
        self.coinbase_base_url = "https://api.coinbase.com/v2"
        self.cryptocom_base_url = "https://api.crypto.com/v2"
        self.max_retries = max_retries
        self.timeout = timeout

    def get_coinbase_data(self, symbol):
        """
        Fetch market data from Coinbase.
        
        Parameters:
            symbol (str): Cryptocurrency symbol.
            
        Returns:
            dict or None: JSON response with market data or None on failure.
        """
        endpoint = f"{self.coinbase_base_url}/prices/{symbol}/spot"
        headers = {"Authorization": f"Bearer {self.coinbase_api_key}"}
        for attempt in range(self.max_retries):
            try:
                response = requests.get(endpoint, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                logging.info(f"Coinbase market data fetched successfully for {symbol}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Coinbase error for {symbol}: {e}. Retry {attempt+1}/{self.max_retries}")
                time.sleep(2 ** attempt)
        return None

    def get_cryptocom_data(self, instrument_name):
        """
        Fetch market data from Crypto.com.
        
        Parameters:
            instrument_name (str): Instrument name (e.g., "BTC_USD").
            
        Returns:
            dict or None: JSON response with market data or None on failure.
        """
        endpoint = f"{self.cryptocom_base_url}/public/get-ticker?instrument_name={instrument_name}"
        for attempt in range(self.max_retries):
            try:
                response = requests.get(endpoint, timeout=self.timeout)
                response.raise_for_status()
                logging.info(f"Crypto.com market data fetched successfully for {instrument_name}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Crypto.com error for {instrument_name}: {e}. Retry {attempt+1}/{self.max_retries}")
                time.sleep(2 ** attempt)
        return None

    def place_coinbase_order(self, symbol, amount, side="buy"):
        """
        Place an order via Coinbase.
        
        Parameters:
            symbol (str): Cryptocurrency symbol.
            amount (float): Order amount.
            side (str): Order side ("buy" or "sell").
            
        Returns:
            dict or None: JSON response with order details or None on failure.
        """
        endpoint = f"{self.coinbase_base_url}/accounts/orders"
        payload = {
            "symbol": symbol,
            "amount": amount,
            "side": side
        }
        headers = {"Authorization": f"Bearer {self.coinbase_api_key}"}
        for attempt in range(2):
            try:
                response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                logging.info(f"Coinbase order placed: {side.upper()} {amount} {symbol}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Coinbase order error for {symbol}: {e}. Retry {attempt+1}/2")
                time.sleep(2 ** attempt)
        return None

    def place_cryptocom_order(self, instrument_name, quantity, side="BUY"):
        """
        Place an order via Crypto.com.
        
        Parameters:
            instrument_name (str): Instrument name (e.g., "BTC_USD").
            quantity (float): Order quantity.
            side (str): Order side (e.g., "BUY" or "SELL").
            
        Returns:
            dict or None: JSON response with order details or None on failure.
        """
        endpoint = f"{self.cryptocom_base_url}/private/create-order"
        payload = {
            "instrument_name": instrument_name,
            "quantity": quantity,
            "side": side,
            "type": "MARKET"
        }
        headers = {"Authorization": f"Bearer {self.cryptocom_api_key}"}
        for attempt in range(2):
            try:
                response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                logging.info(f"Crypto.com order placed: {side.upper()} {quantity} {instrument_name}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Crypto.com order error for {instrument_name}: {e}. Retry {attempt+1}/2")
                time.sleep(2 ** attempt)
        return None

