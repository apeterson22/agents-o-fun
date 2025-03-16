import logging

logging.basicConfig(
    filename='logs/betting_strategy.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def evaluate(betting_data):
    bets = []
    try:
        for event in betting_data:
            if event['favorite_odds'] < 1.5 and event['confidence'] > 80:
                bets.append({
                    'event_id': event['id'],
                    'bet_type': 'favorite_win',
                    'amount': 1000
                })
                logging.info(f"Betting opportunity identified: Event {event['id']}")
    except Exception as e:
        logging.error(f"Error evaluating betting opportunities: {e}")
    return bets
