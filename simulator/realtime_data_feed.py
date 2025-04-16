import logging
import datetime
import pandas as pd
import requests
import yfinance as yf
import json

logger = logging.getLogger("RealTimeDataFeed")

try:
    import ccxt
except ImportError:
    ccxt = None
    logger.warning("ccxt module not installed; crypto live feed will fallback to yfinance.")

class RealTimeDataFeed:
    """
    Provides real-time and historical data for equities, crypto, and forex.
    Uses actual free API endpoints. API keys and settings are taken from configuration.
    """
    def __init__(self, config):
        self.config = config.get("data_feeds", {})
        self.forex_config = self.config.get("forex", {"apiKey": "demo"})
        self.crypto_config = self.config.get("crypto", {"provider": "ccxt", "exchange": "binance", "apiKey": None, "secret": None})

    def update_config(self, new_config):
        self.config.update(new_config)
        logger.info("Data feed config updated: %s", self.config)

    def load_data_equities(self, symbol, start_date, end_date, timeframe):
        try:
            df = yf.download(symbol, start=start_date, end=end_date, interval=timeframe, auto_adjust=True)
            df = df.reset_index()
            df["Symbol"] = symbol
            df = df.rename(columns={"Date": "timestamp", "Close": "close"})
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            logger.info("Equities data loaded for %s: %d rows.", symbol, len(df))
            return df
        except Exception as e:
            logger.error("Error loading equities data for %s: %s", symbol, e)
            return pd.DataFrame()

    def load_data_crypto(self, symbol, start_date, end_date, timeframe):
        if ccxt and self.crypto_config.get("provider") == "ccxt":
            try:
                exchange_id = self.crypto_config.get("exchange", "binance")
                exchange = getattr(ccxt, exchange_id)({
                    "apiKey": self.crypto_config.get("apiKey"),
                    "secret": self.crypto_config.get("secret")
                })
                since = int(pd.to_datetime(start_date).timestamp() * 1000)
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since)
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
                    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                    df["Symbol"] = symbol
                    logger.info("Crypto data (ccxt) loaded for %s: %d rows.", symbol, len(df))
                    return df
            except Exception as e:
                logger.error("Error loading crypto data via ccxt for %s: %s", symbol, e)
        try:
            df = yf.download(symbol, start=start_date, end=end_date, interval=timeframe)
            df = df.reset_index()
            df["Symbol"] = symbol
            df = df.rename(columns={"Date": "timestamp", "Close": "close"})
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            logger.info("Crypto data (yfinance) loaded for %s: %d rows.", symbol, len(df))
            return df
        except Exception as e:
            logger.error("Error loading crypto data for %s: %s", symbol, e)
            return pd.DataFrame()

    def load_data_forex(self, from_symbol, to_symbol, start_date, end_date, timeframe):
        try:
            api_key = self.forex_config.get("apiKey", "demo")
            url = ("https://www.alphavantage.co/query?function=FX_DAILY"
                   f"&from_symbol={from_symbol}&to_symbol={to_symbol}&apikey={api_key}&outputsize=full")
            response = requests.get(url, timeout=10)
            data = response.json()
            if "Time Series FX (Daily)" not in data:
                logger.error("Alpha Vantage error for forex data: %s", data)
                return pd.DataFrame()
            ts = data["Time Series FX (Daily)"]
            records = []
            for date_str, values in ts.items():
                date = pd.to_datetime(date_str)
                if date < pd.to_datetime(start_date) or date > pd.to_datetime(end_date):
                    continue
                records.append({
                    "timestamp": date,
                    "Symbol": f"{from_symbol}-{to_symbol}",
                    "close": float(values["4. close"])
                })
            df = pd.DataFrame(records)
            df.sort_values("timestamp", inplace=True)
            logger.info("Forex data loaded for %s-%s: %d rows.", from_symbol, to_symbol, len(df))
            return df
        except Exception as e:
            logger.error("Error loading forex data for %s-%s: %s", from_symbol, to_symbol, e)
            return pd.DataFrame()

    def get_live_order_book(self, market, symbol):
        if market.lower() == "crypto" and ccxt:
            try:
                exchange_id = self.crypto_config.get("exchange", "binance")
                exchange = getattr(ccxt, exchange_id)({
                    "apiKey": self.crypto_config.get("apiKey"),
                    "secret": self.crypto_config.get("secret")
                })
                order_book = exchange.fetch_order_book(symbol)
                bids = [(bid[0], bid[1]) for bid in order_book.get("bids", [])]
                asks = [(ask[0], ask[1]) for ask in order_book.get("asks", [])]
                from .advanced_order_book import OrderBookModel
                return OrderBookModel(bids=bids, asks=asks, timestamp=datetime.datetime.now())
            except Exception as e:
                logger.error("Error fetching live crypto order book for %s: %s", symbol, e)
        logger.info("Falling back to simulated order book for %s.", symbol)
        from .advanced_order_book import OrderBookModel
        return OrderBookModel()

