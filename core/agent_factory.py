from agents.trading_agent import TradingAgent
from agents.crypto_agent import CryptoAgent
from agents.betting_agent import BettingAgent
from agents.ml_predictor_agent import MLPredictorAgent
from agents.marketing_guru_agent import MarketingGuruAgent

def agent_factory(agent_name):
    agent_map = {
        "trading": TradingAgent,
        "crypto": CryptoAgent,
        "betting": BettingAgent,
        "ml-predictor": MLPredictorAgent,
        "marketing-guru": MarketingGuruAgent
    }
    
    agent_cls = agent_map.get(agent_name)
    if not agent_cls:
        raise ValueError(f"[AgentFactory] Unknown agent type: {agent_name}")
    return agent_cls

