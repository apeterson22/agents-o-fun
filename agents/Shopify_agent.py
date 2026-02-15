from core.agent_registry import register_agent
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

# Setup Logging for ShopifyAgent
logging.basicConfig(filename='shopify_agent.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')
logger = logging.getLogger("ShopifyAgent")

@register_agent("shopify", description="Optimizes Shopify store based on trends and insights", model="LLM", data_source="Google Trends, Shopify Data")
class ShopifyAgent:
    def __init__(self):
        """
        Initialize the ShopifyAgent.
        Loads API credentials from environment variables, sets up Shopify and OpenAI,
        and stores the Google Trends API endpoint.
        """
        SHOP_URL = os.getenv("SHOP_URL")
        API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-01")
        SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
        SHOPIFY_SECRET = os.getenv("SHOPIFY_SECRET")
        SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.GOOGLE_TRENDS_API = os.getenv("GOOGLE_TRENDS_API")
        
        # Shopify API Setup
        shopify.Session.setup(api_key=SHOPIFY_API_KEY, secret=SHOPIFY_SECRET)
        session = shopify.Session(f'{SHOP_URL}', API_VERSION, SHOPIFY_ACCESS_TOKEN)
        shopify.ShopifyResource.activate_session(session)
        logger.info("ShopifyAgent initialized and session activated.")

    def fetch_product_data(self):
        """
        Fetch Shopify product data.
        Returns:
            DataFrame: A pandas DataFrame with product details.
        """
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
        df = pd.DataFrame(product_list)
        logger.info(f"Fetched {len(df)} products from Shopify.")
        return df

    def fetch_market_trends(self):
        """
        Fetch market trends data from the configured Google Trends API.
        Returns:
            dict: Parsed JSON response if successful, otherwise an empty dict.
        """
        try:
            response = requests.get(self.GOOGLE_TRENDS_API)
            if response.status_code == 200:
                logger.info("Market trends data fetched successfully.")
                return response.json()
            else:
                logger.error(f"Failed to fetch market trends data. Status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching market trends data: {e}")
        return {}

    def analyze_trends(self, df, trends_data):
        """
        Use OpenAI's GPT-4 to analyze product and trends data.
        Returns:
            str: A structured response with recommendations.
        """
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
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant specialized in advanced e-commerce optimization."},
                    {"role": "user", "content": prompt}
                ]
            )
            recommendations = response.choices[0].message.content
            logger.info("AI analysis complete; recommendations received.")
            return recommendations
        except Exception as e:
            logger.error(f"Error during OpenAI analysis: {e}")
            return ""

    def adjust_price(self, product_id, new_price):
        """
        Adjust the price of a product in Shopify.
        """
        product = shopify.Product.find(product_id)
        product.variants[0].price = new_price
        product.save()
        logger.info(f"Adjusted price for product ID {product_id} to ${new_price}")

    def adjust_inventory(self, product_id, new_quantity):
        """
        Adjust the inventory quantity of a product in Shopify.
        """
        product = shopify.Product.find(product_id)
        variant = product.variants[0]
        variant.inventory_quantity = new_quantity
        variant.save()
        logger.info(f"Adjusted inventory for product ID {product_id} to {new_quantity}")

    def add_product(self, product_title):
        """
        Add a new product to Shopify.
        """
        product = shopify.Product()
        product.title = product_title
        product.variants = [shopify.Variant({"price": "29.99", "inventory_quantity": 10})]
        product.save()
        logger.info(f"Added product: {product_title}")

    def remove_product(self, product_id):
        """
        Remove a product from Shopify.
        """
        product = shopify.Product.find(product_id)
        product.destroy()
        logger.info(f"Removed product ID: {product_id}")

    def continuous_optimization(self):
        """
        Execute the optimization cycle:
          - Fetch product data and market trends.
          - Analyze data with OpenAI to generate recommendations.
          - Parse recommendations and apply adjustments.
        """
        df = self.fetch_product_data()
        trends_data = self.fetch_market_trends()
        recommendations = self.analyze_trends(df, trends_data)
        logger.info("AI Recommendations:\n" + recommendations)
        lines = recommendations.splitlines()
        try:
            remove_start = lines.index('Products to Remove (poor performance or declining trends):') + 1
            add_start = lines.index('Products to Add (high trending and profitability potential):') + 1
            price_start = lines.index('Suggested price adjustments:') + 1
            inventory_start = lines.index('Inventory suggestions:') + 1
        except ValueError as ve:
            logger.error(f"Error parsing recommendation markers: {ve}")
            return
        remove_products = [line.strip("- ") for line in lines[remove_start:add_start - 1] if line.strip()]
        add_products = [line.strip("- ") for line in lines[add_start:price_start - 1] if line.strip()]
        try:
            price_adjustments = eval('\n'.join(lines[price_start:inventory_start - 1]))
        except Exception as e:
            logger.error(f"Error parsing price adjustments: {e}")
            price_adjustments = {}
        try:
            inventory_suggestions = eval('\n'.join(lines[inventory_start:]))
        except Exception as e:
            logger.error(f"Error parsing inventory suggestions: {e}")
            inventory_suggestions = {}
        for product_name in remove_products:
            product_row = df[df['title'] == product_name]
            if not product_row.empty:
                self.remove_product(product_row.iloc[0]['id'])
        for product_name in add_products:
            self.add_product(product_name)
        for product_name, new_price in price_adjustments.items():
            product_row = df[df['title'] == product_name]
            if not product_row.empty:
                self.adjust_price(product_row.iloc[0]['id'], new_price)
        for product_name, new_quantity in inventory_suggestions.items():
            product_row = df[df['title'] == product_name]
            if not product_row.empty:
                self.adjust_inventory(product_row.iloc[0]['id'], new_quantity)

    def run(self):
        """
        Run the ShopifyAgent continuously by scheduling the optimization
        to execute at a fixed time each day.
        """
        import schedule
        logger.info("ShopifyAgent started: Entering continuous optimization loop.")
        schedule.every().day.at("00:00").do(self.continuous_optimization)
        while True:
            schedule.run_pending()
            time.sleep(60)

