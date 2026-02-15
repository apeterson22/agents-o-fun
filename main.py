# main.py
import logging
import threading
import time
from utils.db_init import init_databases
from staics import create_app
from ai_self_improvement.reinforcement_learning import RLTrainer
from environments.simulated_env import SimulatedTradingEnv
from core.agent_registry import get_registered_agents
from core.agent_loader import load_agents_from_config
from core.agent_manager import AgentManager
from staics import create_app

# Import agents to ensure registration
from agents.trading_agent import TradingAgent
from agents.crypto_agent import CryptoAgent
from agents.betting_agent import BettingAgent
from agents.ml_predictor_agent import MLPredictorAgent
from agents.marketing_guru_agent import MarketingGuruAgent
from agents.network_monitor_agent import NetworkMonitorAgent
from agents.Shopify_agent import ShopifyAgent
from agents.decision_engine_agent import DecisionEngineAgent

logging.basicConfig(
    filename='logs/main_agent.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[logging.FileHandler('logs/main_agent.log'), logging.StreamHandler()]
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def start_trainer():
    try:
        logging.info("RLTrainer thread starting...")
        env = SimulatedTradingEnv()
        trainer = RLTrainer(env)
        trainer.train(total_timesteps=10000)
    except Exception as e:
        logging.exception(f"Trainer thread failed: {e}")

def start_staics_ui():
    try:
        logging.info("Launching STAICS web UI service...")
        app = create_app()
        # expose agent manager if blueprints need it
        app.agent_manager = agent_manager
        app.run(host="0.0.0.0", port=8000)
        logging.info("STAICS interface launched successfully.")
    except Exception as e:
        logging.exception(f"STAICS thread failed: {e}")
        raise

def main():
    logging.info("Initializing databases...")
    init_databases()

    # Load agent configurations
    load_agents_from_config()
    registered_agents = get_registered_agents()
    logging.info(f"Registered Agents: {registered_agents}")

    # Initialize Agent Manager
    manager = AgentManager()

    # Start RL trainer thread
    trainer_thread = threading.Thread(target=start_trainer, daemon=True)
    trainer_thread.start()

    # Start all registered agents
    for agent_id in registered_agents.keys():
        try:
            result = manager.start_agent(agent_id)
            logging.info(f"Started agent {agent_id}: {result}")
        except Exception as e:
            logging.error(f"Failed to start agent {agent_id}: {e}")

    # Start STAICS web interface in a separate thread
    staics_thread = threading.Thread(target=start_staics_ui, daemon=True)
    staics_thread.start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Shutdown signal received. Stopping agents...")
        for agent_id in registered_agents.keys():
            try:
                result = manager.stop_agent(agent_id)
                logging.info(f"Stopped agent {agent_id}: {result}")
            except Exception as e:
                logging.error(f"Error stopping agent {agent_id}: {e}")
        logging.info("All systems shut down cleanly.")

if __name__ == "__main__":
    main()
