# core/agent_factory.py
import logging
from agents.trading_agent import TradingAgent
from agents.crypto_agent import CryptoAgent
from agents.betting_agent import BettingAgent
from agents.ml_predictor_agent import MLPredictorAgent
from agents.marketing_guru_agent import MarketingGuruAgent
from agents.network_monitor_agent import NetworkMonitorAgent
from agents.Shopify_agent import ShopifyAgent
from agents.decision_engine_agent import DecisionEngineAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

def agent_factory(agent_name):
    """
    Factory function to return an agent class based on its name.

    Args:
        agent_name (str): Name of the agent.

    Returns:
        type: Agent class.

    Raises:
        ValueError: If the agent_name is unknown.
    """
    agent_map = {
        "trading": TradingAgent,
        "crypto": CryptoAgent,
        "betting": BettingAgent,
        "ml-predictor": MLPredictorAgent,
        "marketing-guru": MarketingGuruAgent,
        "network-monitoring": NetworkMonitorAgent,
        "shopify": ShopifyAgent,
        "decision-engine": DecisionEngineAgent
    }
    
    agent_cls = agent_map.get(agent_name)
    if not agent_cls:
        logging.error(f"[AgentFactory] Unknown agent type: {agent_name}")
        raise ValueError(f"Unknown agent type: {agent_name}")
    logging.info(f"[AgentFactory] Retrieved class for agent '{agent_name}': {agent_cls.__name__}")
    return agent_cls
