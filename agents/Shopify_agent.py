import shopify
import openai
import pandas as pd
import schedule
import time
import logging
import requests
import json
import os
from datetime import datetime

# Setup Logging
logging.basicConfig(filename='shopify_agent.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Environment Variables
SHOP_URL = os.getenv("SHOP_URL")
API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_SECRET = os.getenv("SHOPIFY_SECRET")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_TRENDS_API = os.getenv("GOOGLE_TRENDS_API")

# Shopify API Setup
shopify.Session.setup(api_key=SHOPIFY_API_KEY, secret=SHOPIFY_SECRET)
session = shopify.Session(f'{SHOP_URL}', API_VERSION, SHOPIFY_ACCESS_TOKEN)
shopify.ShopifyResource.activate_session(session)

# OpenAI Setup
openai.api_key = OPENAI_API_KEY

# Fetch Shopify product data
def fetch_product_data():
    products = shopify.Product.find()
    product_list = []
    for product in products:
        total_inventory = sum([int(variant.inventory_quantity) for variant in product.variants])
        product_list.append({
            'id': product.id,
            'title': product.title,
            'inventory_quantity': total_inventory,
            'price': float(product.variants[0].price),
            'created_at': product.created_at,
            'updated_at': product.updated_at
        })
    return pd.DataFrame(product_list)

# Fetch market trends data from Google Trends API
def fetch_market_trends():
    response = requests.get(GOOGLE_TRENDS_API)
    if response.status_code == 200:
        return response.json()
    logging.error('Failed to fetch market trends data.')
    return {}

# Analyze trends using OpenAI
def analyze_trends(df, trends_data):
    prompt = f"""
    You are tasked with optimizing an e-commerce Shopify store to achieve at least $10,000 in daily profits consistently for 12 months, starting with minimal capital.

    Shopify Data:
    {df.to_csv(index=False)}

    Market Trends Data:
    {json.dumps(trends_data, indent=2)}

    Provide a structured response:
    - Products to Remove (poor performance or declining trends): [list]
    - Products to Add (high trending and profitability potential): [list]
    - Suggested price adjustments: {{'product_title': new_price}}
    - Inventory suggestions: {{'product_title': recommended_inventory_quantity}}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "system", "content": "You are an AI assistant specialized in advanced e-commerce optimization."},
                  {"role": "user", "content": prompt}]
    )
    recommendations = response.choices[0].message.content
    return recommendations

# Dynamic pricing adjustment
def adjust_price(product_id, new_price):
    product = shopify.Product.find(product_id)
    product.variants[0].price = new_price
    product.save()
    logging.info(f"Adjusted price for product ID {product_id} to ${new_price}")

# Adjust inventory quantity
def adjust_inventory(product_id, new_quantity):
    product = shopify.Product.find(product_id)
    variant = product.variants[0]
    variant.inventory_quantity = new_quantity
    variant.save()
    logging.info(f"Adjusted inventory for product ID {product_id} to {new_quantity}")

# Add product to Shopify
def add_product(product_title):
    product = shopify.Product()
    product.title = product_title
    product.variants = [shopify.Variant({"price": "29.99", "inventory_quantity": 10})]
    product.save()
    logging.info(f"Added product: {product_title}")

# Remove product from Shopify
def remove_product(product_id):
    product = shopify.Product.find(product_id)
    product.destroy()
    logging.info(f"Removed product ID: {product_id}")

# Continuous optimization feedback loop
def continuous_optimization():
    df = fetch_product_data()
    trends_data = fetch_market_trends()
    recommendations = analyze_trends(df, trends_data)

    logging.info("AI Recommendations:\n" + recommendations)

    lines = recommendations.splitlines()
    remove_start = lines.index('Products to Remove (poor performance or declining trends):') + 1
    add_start = lines.index('Products to Add (high trending and profitability potential):') + 1
    price_start = lines.index('Suggested price adjustments:') + 1
    inventory_start = lines.index('Inventory suggestions:') + 1

    remove_products = [line.strip("- ") for line in lines[remove_start:add_start - 1] if line.strip()]
    add_products = [line.strip("- ") for line in lines[add_start:price_start - 1] if line.strip()]
    price_adjustments = eval('\n'.join(lines[price_start:inventory_start - 1]))
    inventory_suggestions = eval('\n'.join(lines[inventory_start:]))

    for product_name in remove_products:
        product_row = df[df['title'] == product_name]
        if not product_row.empty:
            remove_product(product_row.iloc[0]['id'])

    for product_name in add_products:
        add_product(product_name)

    for product_name, new_price in price_adjustments.items():
        product_row = df[df['title'] == product_name]
        if not product_row.empty:
            adjust_price(product_row.iloc[0]['id'], new_price)

    for product_name, new_quantity in inventory_suggestions.items():
        product_row = df[df['title'] == product_name]
        if not product_row.empty:
            adjust_inventory(product_row.iloc[0]['id'], new_quantity)

# Scheduler to automate continuous optimization
def schedule_agent():
    schedule.every().day.at("00:00").do(continuous_optimization)

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    schedule_agent()
