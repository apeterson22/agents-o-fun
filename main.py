# main.py

import logging
import threading
from utils.db_init import init_databases
from dashboards.monitoring import launch_dashboard
from ai_self_improvement.reinforcement_learning import RLTrainer
from environments.simulated_env import SimulatedTradingEnv
from core.agent_registry import get_registered_agents
from core.agent_loader import load_agents_from_config

# ✅ Ensure agents are registered BEFORE anything else
from agents.trading_agent import TradingAgent

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

def start_dashboard():
    logging.info("Launching dashboard UI service...")
    launch_dashboard(host="0.0.0.0")

def main():
    logging.info("Initializing databases...")
    init_databases()

    # Load dynamic agent registrations
    load_agents_from_config()
    logging.info(f"Registered Agents: {get_registered_agents()}")

    trainer_thread = threading.Thread(target=start_trainer)
    dashboard_thread = threading.Thread(target=start_dashboard)

    trainer_thread.start()
    dashboard_thread.start()

    trainer_thread.join()
    dashboard_thread.join()

    logging.info("All systems shut down cleanly.")

if __name__ == "__main__":
    main()

