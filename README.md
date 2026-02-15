# agents-o-fun

## Local Ubuntu Multi-Provider AI Agent

This repo now includes a local-first AI supervisor that can orchestrate calls across:

- OpenAI
- Grok/xAI
- Microsoft (Azure OpenAI)
- GitHub Models
- Anthropic

Implemented in `agents/local_ai_supervisor.py` with provider configuration in `agents/local_ai_supervisor.config.json`.

### What it does

- Detects local machine details (CPU, memory, load average, GPU when available).
- Generates runtime tuning recommendations based on available hardware.
- Benchmarks each enabled provider and stores rolling metrics in `state/agent_state.json`.
- Self-optimizes provider routing by selecting the best performing enabled provider over time.

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r agents/requirements.txt
```

Export API keys for the providers you want to enable:

```bash
export OPENAI_API_KEY=...
export GROK_API_KEY=...
export AZURE_OPENAI_API_KEY=...
export GITHUB_TOKEN=...
export ANTHROPIC_API_KEY=...
```

> Note: Microsoft/Azure requires updating the `endpoint` in `agents/local_ai_supervisor.config.json`.

### Usage

Inspect the current system and recommended tuning:

```bash
python agents/local_ai_supervisor.py --config agents/local_ai_supervisor.config.json inspect
```

Benchmark active providers:

```bash
python agents/local_ai_supervisor.py --config agents/local_ai_supervisor.config.json benchmark
```

Run a prompt using the current best provider:

```bash
python agents/local_ai_supervisor.py --config agents/local_ai_supervisor.config.json ask "Summarize my optimization status"
```

Force a specific provider:

```bash
python agents/local_ai_supervisor.py --config agents/local_ai_supervisor.config.json ask "Hello" --provider openai
```
