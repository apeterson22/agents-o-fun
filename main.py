import logging
import threading
import time
from utils.db_init import init_databases
from dashboards.monitoring import launch_dashboard
from ai_self_improvement.reinforcement_learning import RLTrainer
from environments.simulated_env import SimulatedTradingEnv
from core.agent_registry import get_registered_agents
from core.agent_loader import load_agents_from_config
from core.agent_manager import AgentManager

# Import agents to ensure registration via decorators.
from agents.trading_agent import TradingAgent
from agents.crypto_agent import CryptoAgent
from agents.betting_agent import BettingAgent
from agents.ml_predictor_agent import MLPredictorAgent
from agents.marketing_guru_agent import MarketingGuruAgent
from agents.network_monitor_agent import NetworkMonitorAgent
from agents.Shopify_agent import *  # Adjust if specific symbols needed
from agents.decision_engine_agent import DecisionEngineAgent

logging.basicConfig(
    filename='logs/main_agent.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

def start_trainer():
    try:
        logging.info("RLTrainer thread starting...")
        env = SimulatedTradingEnv()
        trainer = RLTrainer(env)
        trainer.train(total_timesteps=10000)
    except Exception as e:
        logging.exception(f"Trainer thread failed: {e}")

def start_dashboard(agent_manager):
    try:
        logging.info("Launching dashboard UI service...")
        launch_dashboard(agent_manager=agent_manager, host="0.0.0.0")
    except Exception as e:
        logging.exception(f"Dashboard thread failed: {e}")

def main():
    logging.info("Initializing databases...")
    init_databases()

    # Load dynamic agent registrations (from config file and decorators)
    load_agents_from_config()
    registered_agents = get_registered_agents()
    logging.info(f"Registered Agents: {registered_agents}")

    # Initialize the Agent Manager to control agents.
    manager = AgentManager()

    # Start dashboard and RL trainer threads.
    dashboard_thread = threading.Thread(target=start_dashboard, args=(manager,), daemon=True)
    trainer_thread = threading.Thread(target=start_trainer, daemon=True)

    dashboard_thread.start()
    trainer_thread.start()

    # Start all registered agents using the Agent Manager.
    for agent_id in registered_agents.keys():
        try:
            result = manager.start_agent(agent_id)
            logging.info(f"Started agent {agent_id}: {result}")
        except Exception as e:
            logging.error(f"Failed to start agent {agent_id}: {e}")

    # Keep the main thread alive, allowing for graceful shutdown.
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

