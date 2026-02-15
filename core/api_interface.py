import requests
import logging
import time

logging.basicConfig(
    filename='logs/fidelity_api.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class FidelityAPI:
    def __init__(self, api_key, base_url="https://api.fidelity.com", max_retries=3, timeout=10):
        """
        Initialize the FidelityAPI interface.
        
        Parameters:
            api_key (str): API key for accessing Fidelity's endpoints.
            base_url (str): Base URL for the Fidelity API.
            max_retries (int): Maximum number of retries for each request.
            timeout (int): Request timeout in seconds.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.max_retries = max_retries
        self.timeout = timeout

    def get_market_data(self, symbol):
        """
        Retrieve market data for a given symbol.
        
        Parameters:
            symbol (str): Stock or asset symbol.
            
        Returns:
            dict or None: JSON response with market data, or None if the request fails.
        """
        endpoint = f"{self.base_url}/marketdata/{symbol}"
        for attempt in range(self.max_retries):
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                logging.info(f"Market data fetched successfully for {symbol}.")
                return response.json()
            except requests.exceptions.HTTPError as e:
                logging.error(f"HTTP error fetching market data for {symbol}: {e}")
            except requests.exceptions.ConnectionError as e:
                logging.error(f"Connection error fetching market data for {symbol}: {e}")
            except requests.exceptions.Timeout as e:
                logging.warning(f"Timeout fetching market data for {symbol}: {e}. Retrying ({attempt+1}/{self.max_retries})...")
                time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                logging.critical(f"Unexpected error fetching market data for {symbol}: {e}")
                break
        return None

    def place_order(self, symbol, quantity, order_type="market", side="buy"):
        """
        Place an order for a given symbol.
        
        Parameters:
            symbol (str): The asset symbol.
            quantity (int or float): Quantity to trade.
            order_type (str): Type of order ("market" by default).
            side (str): Side of the trade ("buy" or "sell").
            
        Returns:
            dict or None: JSON response with order details, or None if the order fails.
        """
        endpoint = f"{self.base_url}/orders"
        payload = {
            "symbol": symbol,
            "quantity": quantity,
            "type": order_type,
            "side": side
        }
        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=self.timeout)
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

