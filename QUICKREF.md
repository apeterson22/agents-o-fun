# Quick Reference Guide

## Starting the System

### Quick Start (All Components)
```bash
./start.sh
```

### Individual Components

**Trading Agent:**
```bash
python3 main.py
```

**OpenClaw Gateway:**
```bash
npm start
```

**Shopify Agent:**
```bash
cd agents && python3 Shopify_agent.py
```

## Common Tasks

### Trading Agent

**Get Statistics:**
```bash
python3 skills/trading-agent/scripts/get_stats.py
# or
curl http://localhost:8081/stats
```

**Trigger Training:**
```bash
python3 skills/trading-agent/scripts/trigger_training.py
# or
curl -X POST http://localhost:8081/train
```

**Reload Model:**
```bash
python3 skills/trading-agent/scripts/reload_model.py
# or
curl -X POST http://localhost:8081/reload-model
```

### Shopify Agent

**Run Optimization:**
```bash
python3 skills/shopify-agent/scripts/run_optimization.py
```

### OpenClaw

**Send Message to Agent:**
```bash
npx openclaw agent --message "Your message here" --thinking high
```

**List Skills:**
```bash
npx openclaw skills list
```

**Check System Health:**
```bash
npx openclaw doctor
```

## Endpoints

- **Trading Agent API:** http://localhost:8081
- **Trading Dashboard:** http://localhost:8050
- **OpenClaw Gateway:** http://localhost:18789

## API Endpoints

### Trading Agent (Port 8081)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stats` | GET | Get current statistics |
| `/stats/raw` | GET | Get raw statistics |
| `/train` | POST | Trigger training |
| `/reload-model` | POST | Reload the model |
| `/checkpoint` | POST | Save checkpoint |
| `/initialize` | POST | Initialize modules |

## Logs

- Trading Agent: `logs/trading-agent.log` or `logs/main_agent.log`
- OpenClaw: `logs/openclaw-gateway.log`
- Shopify Agent: `shopify_agent.log`

## Testing

**Run Integration Tests:**
```bash
python3 test_integration.py
```

**Run Individual Tests:**
```bash
npm test
```

## Troubleshooting

**Services won't start:**
```bash
# Check if ports are in use
lsof -i :8081  # Trading Agent
lsof -i :8050  # Dashboard
lsof -i :18789 # OpenClaw

# Kill processes if needed
kill <PID>
```

**Dependencies missing:**
```bash
npm install
pip3 install -r requirements.txt
```

**Environment not configured:**
```bash
cp .env.openclaw .env
# Edit .env with your API keys
```

## Configuration Files

- `.env` - Environment variables (API keys, tokens)
- `config.ini` - Trading agent configuration
- `package.json` - Node.js/OpenClaw configuration
- `requirements.txt` - Python dependencies

## Getting Help

1. Check `SETUP.md` for detailed setup instructions
2. Check `README.md` for architecture overview
3. Review logs in `logs/` directory
4. Run integration tests: `python3 test_integration.py`

## NPM Scripts

```bash
npm run setup        # Run OpenClaw onboarding
npm start            # Start OpenClaw gateway
npm run start:all    # Start all components (uses ./start.sh)
npm test             # Run integration tests
npm run trading      # Start trading agent only
npm run shopify      # Start Shopify agent only
```
