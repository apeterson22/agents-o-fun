---
name: trading-agent
description: "AI-powered trading agent with RL training, genetic optimization, and multi-market support (stocks, crypto, betting). Manages positions, risk, and compliance."
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["python3"], "env": ["AI_API_KEY"] },
        "install":
          [
            {
              "id": "python-brew",
              "kind": "brew",
              "formula": "python",
              "bins": ["python3"],
              "label": "Install Python (brew)",
            },
            {
              "id": "python-apt",
              "kind": "apt",
              "package": "python3",
              "bins": ["python3"],
              "label": "Install Python (apt)",
            },
          ],
      },
  }
---

# Trading Agent Skill

AI-powered trading agent with reinforcement learning, genetic algorithm optimization, and multi-market support.

## Features

- **Multi-Market Trading**: Supports Fidelity (stocks), Crypto.com/Coinbase (crypto), and betting markets
- **AI-Powered**: Uses reinforcement learning (RL) and genetic algorithms (GA) for strategy optimization
- **Risk Management**: Automated stop-loss, position sizing, and daily loss limits
- **Regulatory Compliance**: Built-in compliance checks
- **Real-time Monitoring**: Web dashboard on port 8050
- **Training Mode**: Generate synthetic data and train models

## Prerequisites

The trading agent requires Python dependencies to be installed:

```bash
cd {baseDir}
pip3 install -r requirements.txt
```

## API Endpoints

The trading agent runs a FastAPI server on port 8081:

### Get Stats

```bash
python3 {baseDir}/scripts/get_stats.py
```

### Get Raw Stats

```bash
python3 {baseDir}/scripts/get_raw_stats.py
```

### Trigger Training

```bash
python3 {baseDir}/scripts/trigger_training.py
```

### Reload Model

```bash
python3 {baseDir}/scripts/reload_model.py
```

### Save Checkpoint

```bash
python3 {baseDir}/scripts/save_checkpoint.py
```

### Initialize Modules

```bash
python3 {baseDir}/scripts/initialize_modules.py
```

## Start the Agent

The trading agent runs as a background service:

```bash
cd {baseDir}
python3 main.py &
```

Access the dashboard at http://localhost:8050

## Environment Variables

Required environment variables (set in `.env`):

- `FIDELITY_API_KEY`: Fidelity trading API key
- `COINBASE_KEY`: Coinbase API key
- `CRYPTOCOM_KEY`: Crypto.com API key
- `CRYPTOCOM_BETTING_KEY`: Crypto.com betting API key
- `AI_API_KEY`: AI provider API key (for OpenAI or Ollama)

## Configuration

Edit `config.ini` to customize:

- Daily profit goals
- Risk limits (max daily loss, stop loss %, max position size)
- AI provider settings (ollama vs openai)

## Examples

Check current trading stats:
```bash
python3 {baseDir}/scripts/get_stats.py
```

Train the RL model:
```bash
python3 {baseDir}/scripts/trigger_training.py
```

Reload the model after training:
```bash
python3 {baseDir}/scripts/reload_model.py
```
