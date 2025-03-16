import logging
import requests

logging.basicConfig(
    filename='logs/private_feed.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def fetch_data(urls, headers):
    data = {}
    try:
        for url in urls:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data[url] = response.json()
            logging.info(f"Fetched private data from {url}")
    except Exception as e:
        logging.error(f"Error fetching private data: {e}")
    return data
