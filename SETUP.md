# OpenClaw Integration Setup Guide

This guide walks you through setting up the agents-o-fun platform with OpenClaw as the primary agent orchestrator.

## Architecture Overview

The system consists of three main components:

1. **OpenClaw Gateway** - Primary agent orchestrator (Node.js/TypeScript)
2. **Trading Agent** - Multi-market trading with RL/GA optimization (Python)
3. **Shopify Agent** - E-commerce optimization (Python)

OpenClaw acts as the central hub that coordinates and invokes specialized Python agents through its skill system.

## Prerequisites

### Required Software

- **Node.js** >= 22 ([Download](https://nodejs.org/))
- **Python** >= 3.10
- **pip3** (Python package manager)
- **npm** (Node.js package manager, comes with Node.js)

### Verify Installation

```bash
node --version  # Should be >= 22
python3 --version  # Should be >= 3.10
npm --version
pip3 --version
```

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/apeterson22/agents-o-fun.git
cd agents-o-fun
```

### 2. Install Dependencies

Install both Node.js and Python dependencies:

```bash
# Install Node.js dependencies (OpenClaw)
npm install

# Install Python dependencies (Agents)
pip3 install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.openclaw .env
```

Edit `.env` and fill in your API keys:

```env
# OpenClaw
OPENCLAW_GATEWAY_TOKEN=your-secure-token-here

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...  # optional

# Trading APIs
FIDELITY_API_KEY=...
COINBASE_KEY=...
CRYPTOCOM_KEY=...
CRYPTOCOM_BETTING_KEY=...

# Shopify (optional, if using Shopify agent)
SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=...
SHOPIFY_API_KEY=...
SHOPIFY_SECRET=...
```

### 4. Set Up OpenClaw

Run the OpenClaw onboarding wizard:

```bash
npm run setup
```

Follow the prompts to:
- Configure AI model providers (OpenAI, Anthropic, etc.)
- Set up messaging channels (optional: WhatsApp, Telegram, etc.)
- Configure skills and permissions

### 5. Configure Trading Agent

Edit `config.ini` to set your trading parameters:

```ini
[Goals]
daily_profit = 10000

[Risk]
max_daily_loss = 5000
stop_loss_pct = 0.03
max_position_size = 2000

[AI]
provider = ollama  # or openai
endpoint = http://0.0.0.0:11434
model = deepseek-r1:8b
```

## Running the System

### Option 1: Use the Start Script (Recommended)

The easiest way to start all components:

```bash
./start.sh
```

This starts:
- Trading Agent API (port 8081)
- Trading Dashboard (port 8050)
- OpenClaw Gateway (port 18789)

Press Ctrl+C to stop all services.

### Option 2: Manual Start

Start each component in separate terminal windows:

**Terminal 1 - Trading Agent:**
```bash
python3 main.py
```

**Terminal 2 - OpenClaw Gateway:**
```bash
npm start
# or: npx openclaw gateway --port 18789 --verbose
```

**Terminal 3 - Shopify Agent (Optional):**
```bash
cd agents
python3 Shopify_agent.py
```

## Verifying the Installation

### 1. Check Services are Running

```bash
# Trading Agent API
curl http://localhost:8081/stats

# Trading Dashboard (open in browser)
open http://localhost:8050

# OpenClaw Gateway (requires auth)
curl http://localhost:18789/health
```

### 2. Run Integration Tests

```bash
python3 test_integration.py
```

This will test that all API endpoints are accessible.

### 3. Test OpenClaw Skills

```bash
# Get trading stats via skill
python3 skills/trading-agent/scripts/get_stats.py

# Trigger training
python3 skills/trading-agent/scripts/trigger_training.py

# Run Shopify optimization (if configured)
python3 skills/shopify-agent/scripts/run_optimization.py
```

### 4. Test via OpenClaw CLI

```bash
# Send a message to the agent
npx openclaw agent --message "Get current trading stats" --thinking high

# Check available skills
npx openclaw skills list
```

## Using the System

### Via OpenClaw CLI

OpenClaw provides a unified interface to all agents:

```bash
# Get trading statistics
npx openclaw agent --message "What are the current trading stats?"

# Trigger model training
npx openclaw agent --message "Train the trading model"

# Optimize Shopify store
npx openclaw agent --message "Run Shopify store optimization"
```

### Via Direct API Calls

You can also call agent APIs directly:

```bash
# Trading Agent
curl http://localhost:8081/stats
curl -X POST http://localhost:8081/train
curl -X POST http://localhost:8081/reload-model

# Access the dashboard
open http://localhost:8050
```

### Via Skills

Each agent has a skill directory with helper scripts:

```bash
# Trading Agent Skills
ls skills/trading-agent/scripts/
python3 skills/trading-agent/scripts/get_stats.py
python3 skills/trading-agent/scripts/trigger_training.py

# Shopify Agent Skills
ls skills/shopify-agent/scripts/
python3 skills/shopify-agent/scripts/run_optimization.py
```

## Troubleshooting

### OpenClaw Won't Start

1. Check Node.js version: `node --version` (must be >= 22)
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check logs: `cat logs/openclaw-gateway.log`

### Trading Agent Won't Start

1. Check Python version: `python3 --version` (must be >= 3.10)
2. Install dependencies: `pip3 install -r requirements.txt`
3. Check environment variables in `.env`
4. Check logs: `cat logs/trading-agent.log` or `cat logs/main_agent.log`

### API Connection Errors

1. Ensure all services are running
2. Check ports aren't blocked or in use:
   ```bash
   lsof -i :8081  # Trading Agent
   lsof -i :8050  # Dashboard
   lsof -i :18789 # OpenClaw
   ```
3. Verify firewall settings

### Skill Execution Fails

1. Ensure agent APIs are running and accessible
2. Check script permissions: `chmod +x skills/*/scripts/*.py`
3. Verify Python path is correct in scripts
4. Check environment variables are set

## Next Steps

- **Configure Messaging Channels**: Set up WhatsApp, Telegram, or Slack integration in OpenClaw
- **Add Custom Skills**: Create new skills in `skills/` directory
- **Customize Trading Strategies**: Edit strategies in `strategies/` directory
- **Train Models**: Use the training mode to optimize trading algorithms
- **Monitor Performance**: Use the dashboard at http://localhost:8050

## Additional Resources

- [OpenClaw Documentation](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [Project Repository](https://github.com/apeterson22/agents-o-fun)

## Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Run the integration test: `python3 test_integration.py`
3. Open an issue on GitHub
