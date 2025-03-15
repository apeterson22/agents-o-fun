# Dockerfile for Shopify AI Agent

# Base Python Image
FROM python:3.11-slim

# Working Directory
WORKDIR /app

# Install Dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy Source Code
COPY . /app

# Environment Variables (passed securely at runtime)
# Required Environment Variables:
# SHOP_URL: your-store.myshopify.com (e.g., my-store.myshopify.com)
# SHOPIFY_API_VERSION: Shopify API version (e.g., "2024-01")
# SHOPIFY_API_KEY: Shopify App API key (from Shopify admin)
# SHOPIFY_SECRET: your Shopify app's API secret key
# SHOPIFY_ACCESS_TOKEN: your Shopify private app's access token
# OPENAI_API_KEY: your OpenAI API key
# GOOGLE_TRENDS_API: URL to your market trends data API

# Example (to pass at runtime):
# docker run -d --env SHOP_URL='your-store.myshopify.com' \
#                --env SHOPIFY_API_KEY='your_api_key' \
#                --env SHOPIFY_SECRET='your_secret' \
#                --env SHOPIFY_ACCESS_TOKEN='your_access_token' \
#                --env OPENAI_API_KEY='your_openai_key' \
#                --env GOOGLE_TRENDS_API='https://api.yourtrends.com/data' \
#                your-image-name

# Command to run the agent
CMD ["python", "your_agent_script.py"]
