# core/agent_factory.py

from agents.trading_agent import TradingAgent
from agents.crypto_agent import CryptoAgent
from agents.betting_agent import BettingAgent
from agents.ml_predictor_agent import MLPredictorAgent
from agents.marketing_guru_agent import MarketingGuruAgent
from agents.network_monitor_agent import NetworkMonitorAgent
from agents.Shopify_agent import ShopifyAgent
from agents.decision_engine_agent import DecisionEngineAgent

def agent_factory(agent_name):
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
        raise ValueError(f"[AgentFactory] Unknown agent type: {agent_name}")
    return agent_cls

