import os

## Project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

## Folders
DATABASE_FOLDER = os.path.join(BASE_DIR, "databases")
AGENTS_FOLDER = os.path.join(BASE_DIR, "agents")
STRATEGIES_FOLDER = os.path.join(BASE_DIR, "strategies")
DASHBOARDS_FOLDER = os.path.join(BASE_DIR, "dashboards")
MODELS_FOLDER = os.path.join(BASE_DIR, "models")
PLUGINS_FOLDER = os.path.join(BASE_DIR, "plugins")
ENVIRONMENTS_FOLDER = os.path.join(BASE_DIR, "environments")
AI_SI_FOLDER = os.path.join(BASE_DIR, "ai_self_improvement")
LOGS_FOLDER = os.path.join(BASE_DIR, "logs")
FEATURES_FOLDER = os.path.join(BASE_DIR, "features")
DATA_FOLDER = os.path.join(BASE_DIR, "data")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
TRAINING_EXPORTS_FOLDER = os.path.join(BASE_DIR, "training_exports")

## Databases
TRADES_DB = os.path.join(DATABASE_FOLDER, "trades.db")
TRAINING_DATA_DB = os.path.join(DATABASE_FOLDER, "training_data.db")

## Agents
AGENT_MODELS_FOLDER = os.path.join(MODELS_FOLDER, "agents")
AGENT_LOGS_FOLDER = os.path.join(LOGS_FOLDER, "agents")
AGENT_DATA_FOLDER = os.path.join(DATABASE_FOLDER, "agents")

