# agents-o-fun

AI-powered trading and e-commerce automation platform built on **OpenClaw** - an open-source agent orchestration framework.

## 🦞 OpenClaw Integration

This project uses [OpenClaw](https://github.com/openclaw/openclaw) as the primary agent orchestrator, with specialized agents for:

- **📈 Trading Agent**: AI-powered multi-market trading (stocks, crypto, betting) with RL/GA optimization
- **🛍️ Shopify Agent**: E-commerce optimization with automated pricing and inventory management

## Quick Start

### Prerequisites

- **Node.js** ≥22 (for OpenClaw)
- **Python** ≥3.10 (for specialized agents)
- API keys for your trading/e-commerce platforms

### Installation

1. **Install OpenClaw and dependencies**:
   ```bash
   npm install
   pip install -r requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.openclaw .env
   # Edit .env with your API keys
   ```

3. **Set up OpenClaw**:
   ```bash
   npm run setup
   # Follow the onboarding wizard
   ```

4. **Start the system**:
   ```bash
   # Terminal 1: Start OpenClaw gateway
   npm start

   # Terminal 2: Start Trading Agent
   python3 main.py

   # Terminal 3: Start Shopify Agent (optional)
   cd agents
   python3 Shopify_agent.py
   ```

## Architecture

### OpenClaw as Primary Orchestrator

OpenClaw runs as the main gateway and agent runtime, providing:
- Multi-channel messaging integration (WhatsApp, Telegram, Slack, Discord, etc.)
- Unified agent interface
- Skill-based extensibility
- Persistent memory and context
- Model-agnostic LLM integration

### Specialized Python Agents

Python agents run as microservices with REST APIs that OpenClaw skills can invoke:

```
┌─────────────────────────────────────────┐
│         OpenClaw Gateway                │
│    (Agent Orchestrator & Router)        │
└─────────┬───────────────────────────────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
┌─────────┐ ┌──────────┐
│ Trading │ │ Shopify  │
│ Agent   │ │ Agent    │
│ Skill   │ │ Skill    │
└────┬────┘ └────┬─────┘
     │           │
     │ HTTP API  │ HTTP API
     │           │
     ▼           ▼
┌─────────┐ ┌──────────┐
│ Trading │ │ Shopify  │
│ Agent   │ │ Agent    │
│ (Python)│ │ (Python) │
└─────────┘ └──────────┘
```

## Using the Agents

### Via OpenClaw CLI

```bash
# Get trading statistics
openclaw agent --message "Get current trading stats" --thinking high

# Trigger model training
openclaw agent --message "Train the trading model" --thinking high

# Optimize Shopify store
openclaw agent --message "Run Shopify optimization" --thinking high
```

### Via Skills API (Direct)

```bash
# Trading Agent
python3 skills/trading-agent/scripts/get_stats.py
python3 skills/trading-agent/scripts/trigger_training.py

# Shopify Agent
python3 skills/shopify-agent/scripts/run_optimization.py
```

### Via REST API (Direct)

```bash
# Trading Agent API (port 8081)
curl http://localhost:8081/stats
curl -X POST http://localhost:8081/train

# Dashboard
open http://localhost:8050
```

## Configuration

### Trading Agent (`config.ini`)

```ini
[Goals]
daily_profit = 10000

[Risk]
max_daily_loss = 5000
stop_loss_pct = 0.03
max_position_size = 2000

[AI]
provider = ollama
endpoint = http://0.0.0.0:11434
model = deepseek-r1:8b
```

### OpenClaw Skills

Skills are located in `skills/` directory:
- `skills/trading-agent/` - Trading automation skill
- `skills/shopify-agent/` - E-commerce optimization skill

Each skill includes:
- `SKILL.md` - Skill documentation and metadata
- `scripts/` - Python helper scripts for the skill

## Development

### Adding New Agents

1. Create a new skill directory: `skills/your-agent/`
2. Add `SKILL.md` with OpenClaw metadata
3. Create helper scripts in `scripts/`
4. Make your agent expose a REST API (optional but recommended)
5. Update `.env.openclaw` with required environment variables

### Project Structure

```
agents-o-fun/
├── skills/              # OpenClaw skills
│   ├── trading-agent/   # Trading automation skill
│   └── shopify-agent/   # Shopify optimization skill
├── agents/              # Legacy agent implementations
│   └── Shopify_agent.py
├── core/                # Trading engine core
├── strategies/          # Trading strategies
├── ai_self_improvement/ # RL/GA optimization
├── main.py             # Trading agent entry point
├── package.json        # OpenClaw/Node.js config
└── requirements.txt    # Python dependencies
```

## License

MIT