import requests
import logging
import time

logging.basicConfig(
    filename='logs/betting_api.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class BettingAPI:
    def __init__(self, cryptocom_api_key, max_retries=3, timeout=10):
        """
        Initialize the BettingAPI interface.
        
        Parameters:
            cryptocom_api_key (str): API key for Crypto.com's betting endpoint.
            max_retries (int): Maximum number of retries for requests.
            timeout (int): Request timeout in seconds.
        """
        self.api_key = cryptocom_api_key
        self.base_url = "https://api.crypto.com/betting/v1"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.max_retries = max_retries
        self.timeout = timeout

    def get_betting_odds(self, event_id):
        """
        Retrieve betting odds for a given event with exponential back-off.
        
        Parameters:
            event_id (str): Identifier for the event.
            
        Returns:
            dict or None: JSON response on success, or None if all retries fail.
        """
        endpoint = f"{self.base_url}/odds/{event_id}"
        for attempt in range(self.max_retries):
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                logging.info(f"Fetched odds successfully for event {event_id}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching odds for event {event_id}: {e}. Retry {attempt+1}/{self.max_retries}")
                time.sleep(2 ** attempt)  # Exponential back-off
        return None

    def place_bet(self, event_id, bet_type, amount):
        """
        Place a bet using the Crypto.com betting API.
        
        Parameters:
            event_id (str): Identifier for the event.
            bet_type (str): Type of bet (e.g., "back" or "lay").
            amount (float): Bet amount.
            
        Returns:
            dict or None: JSON response on success, or None if all retries fail.
        """
        endpoint = f"{self.base_url}/bets"
        payload = {
            "event_id": event_id,
            "bet_type": bet_type,
            "amount": amount
        }
        for attempt in range(2):  # Two retries for placing bets
            try:
                response = requests.post(endpoint, json=payload, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                logging.info(f"Placed bet: {bet_type} ${amount} on event {event_id}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Betting error on event {event_id}: {e}. Retry {attempt+1}/2")
                time.sleep(2 ** attempt)
        return None

