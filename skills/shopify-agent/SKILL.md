---
name: shopify-agent
description: "AI-powered Shopify e-commerce optimization agent. Analyzes product performance, market trends, and automatically optimizes pricing, inventory, and product catalog."
metadata:
  {
    "openclaw":
      {
        "emoji": "🛍️",
        "requires": { "bins": ["python3"], "env": ["SHOPIFY_ACCESS_TOKEN", "OPENAI_API_KEY"] },
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

# Shopify Agent Skill

AI-powered e-commerce optimization agent for Shopify stores using GPT-4 for intelligent product management.

## Features

- **Product Performance Analysis**: Analyzes sales data and inventory levels
- **Market Trend Integration**: Uses Google Trends API for market insights
- **Automated Pricing**: AI-driven dynamic pricing optimization
- **Inventory Management**: Automatic inventory quantity adjustments
- **Product Catalog Optimization**: Adds trending products, removes underperformers
- **Continuous Optimization**: Scheduled daily optimization runs

## Prerequisites

Install Python dependencies:

```bash
cd {baseDir}/../agents
pip3 install -r requirements.txt
```

## Environment Variables

Required environment variables (set in `.env`):

- `SHOP_URL`: Your Shopify store URL
- `SHOPIFY_API_VERSION`: Shopify API version (default: "2024-01")
- `SHOPIFY_API_KEY`: Shopify API key
- `SHOPIFY_SECRET`: Shopify API secret
- `SHOPIFY_ACCESS_TOKEN`: Shopify access token
- `OPENAI_API_KEY`: OpenAI API key (for GPT-4)
- `GOOGLE_TRENDS_API`: Google Trends API endpoint

## Run Optimization

Run a single optimization cycle:

```bash
python3 {baseDir}/scripts/run_optimization.py
```

## Start Scheduler

Run the agent in continuous mode with daily optimization at midnight:

```bash
cd {baseDir}/../agents
python3 Shopify_agent.py
```

## How It Works

1. **Fetch Data**: Retrieves product data from Shopify and market trends from Google Trends
2. **AI Analysis**: Uses GPT-4 to analyze data and generate recommendations
3. **Execute Actions**: Automatically implements recommended changes:
   - Remove underperforming products
   - Add trending products
   - Adjust prices based on market conditions
   - Optimize inventory levels

## Examples

Run a one-time optimization:
```bash
python3 {baseDir}/scripts/run_optimization.py
```

The agent will analyze your store and output AI recommendations before making changes.

## Notes

- The agent requires valid Shopify API credentials with appropriate permissions
- Price and inventory changes are applied automatically - review recommendations carefully
- Daily optimization runs at midnight (configurable in the agent code)
- Logs are written to `shopify_agent.log`
