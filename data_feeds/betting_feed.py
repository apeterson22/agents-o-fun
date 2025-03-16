import logging
from core.betting_interface import BettingAPI

logging.basicConfig(
    filename='logs/betting_feed.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def fetch_data(event_ids, cryptocom_api_key):
    api = BettingAPI(cryptocom_api_key)
    data = {}
    try:
        for event_id in event_ids:
            odds_data = api.get_betting_odds(event_id)
            if odds_data:
                data[event_id] = odds_data
                logging.info(f"Fetched betting odds for event {event_id}")
            else:
                logging.warning(f"No betting odds data received for event {event_id}")
    except Exception as e:
        logging.error(f"Error fetching betting odds data: {e}")
    return data
