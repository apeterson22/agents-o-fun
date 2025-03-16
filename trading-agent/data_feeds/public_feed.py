import logging
import requests

logging.basicConfig(
    filename='logs/public_feed.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def fetch_data(urls):
    data = {}
    try:
        for url in urls:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data[url] = response.json()
            logging.info(f"Fetched public data from {url}")
    except Exception as e:
        logging.error(f"Error fetching public data: {e}")
    return data
