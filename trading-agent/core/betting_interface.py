import requests
import logging
import time

logging.basicConfig(
    filename='logs/betting_api.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

class BettingAPI:
    def __init__(self, cryptocom_api_key):
        self.api_key = cryptocom_api_key
        self.base_url = "https://api.crypto.com/betting/v1"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def get_betting_odds(self, event_id, retries=3):
        endpoint = f"{self.base_url}/odds/{event_id}"
        for attempt in range(retries):
            try:
                response = requests.get(endpoint, headers=self.headers, timeout=10)
                response.raise_for_status()
                logging.info(f"Fetched odds successfully for event {event_id}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Error fetching odds for event {event_id}: {e}, Retry {attempt+1}/{retries}")
                time.sleep(2 ** attempt)
        return None

    def place_bet(self, event_id, bet_type, amount, retries=2):
        endpoint = f"{self.base_url}/bets"
        payload = {
            "event_id": event_id,
            "bet_type": bet_type,
            "amount": amount
        }
        for attempt in range(retries):
            try:
                response = requests.post(endpoint, json=payload, headers=self.headers, timeout=10)
                response.raise_for_status()
                logging.info(f"Placed bet: {bet_type} ${amount} on event {event_id}.")
                return response.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Betting error on event {event_id}: {e}, Retry {attempt+1}/{retries}")
                time.sleep(2 ** attempt)
        return None

