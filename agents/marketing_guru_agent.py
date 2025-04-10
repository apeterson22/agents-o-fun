import logging
import sqlite3
from datetime import datetime
from pytrends.request import TrendReq
import pandas as pd

from core.agent_registry import register_agent

log = logging.getLogger(__name__)
DB_PATH = "databases/training_data.db"

@register_agent("marketing-guru", description="AI agent for running marketing analysis and strategy", model="LLM", data_source="Google Trends, Keywords")
class MarketingGuruAgent:
    def __init__(self, keywords=None, timeframe="now 1-d", geo="", gprop="", hl="en-US", tz=360):
        """
        Initialize the MarketingGuruAgent.
        
        Parameters:
            keywords (list): List of keywords to track. Defaults to ["AI", "Crypto", "Fitness", "Sustainability"].
            timeframe (str): Timeframe for trend analysis (e.g., "now 1-d").
            geo (str): Geographical region code for filtering trends.
            gprop (str): Google property (e.g., images, news) to filter trends.
            hl (str): Host language.
            tz (int): Timezone offset.
        """
        self.pytrends = TrendReq(hl=hl, tz=tz)
        self.keywords = keywords if keywords is not None else ["AI", "Crypto", "Fitness", "Sustainability"]
        self.timeframe = timeframe
        self.geo = geo
        self.gprop = gprop

    def fetch_trends(self):
        """
        Fetch marketing trends using the Google Trends API for the configured keywords.
        
        Returns:
            DataFrame: A pandas DataFrame with trends data.
        """
        try:
            self.pytrends.build_payload(self.keywords, cat=0, timeframe=self.timeframe, geo=self.geo, gprop=self.gprop)
            df = self.pytrends.interest_over_time()
            if df.empty:
                log.warning("[MARKETING AGENT] No trend data returned.")
            return df
        except Exception as e:
            log.error(f"[MARKETING AGENT] Failed to fetch trends: {e}")
            return pd.DataFrame()

    def analyze_trends(self, df):
        """
        Analyze the trends data to derive insights.
        
        Returns:
            dict: A summary of insights including average interest, momentum, and the top trending keyword.
        """
        analysis = {}
        try:
            if df.empty:
                log.warning("[MARKETING AGENT] No data to analyze.")
                return analysis
            
            # Compute average interest per keyword
            avg_interest = df[self.keywords].mean()
            analysis["average_interest"] = avg_interest.to_dict()
            
            # Compute momentum (difference between the last and first recorded interest for each keyword)
            momentum = {}
            for kw in self.keywords:
                try:
                    first_val = df[kw].iloc[0]
                    last_val = df[kw].iloc[-1]
                    momentum[kw] = last_val - first_val
                except Exception as e:
                    momentum[kw] = None
                    log.error(f"[MARKETING AGENT] Error calculating momentum for {kw}: {e}")
            analysis["momentum"] = momentum
            
            # Identify the top trending keyword based on the highest average interest
            top_keyword = avg_interest.idxmax()
            analysis["top_keyword"] = top_keyword
            analysis["top_keyword_avg_interest"] = avg_interest[top_keyword]
            
            log.info(f"[MARKETING AGENT] Trend Analysis: {analysis}")
        except Exception as e:
            log.error(f"[MARKETING AGENT] Failed to analyze trends: {e}")
        return analysis

    def save_to_db(self, df):
        """
        Save the trends data into the database.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marketing_trends (
                    timestamp TEXT,
                    keyword TEXT,
                    interest INTEGER
                )
            """)
            for index, row in df.iterrows():
                timestamp = index.to_pydatetime().isoformat()
                for kw in self.keywords:
                    try:
                        interest_val = int(row[kw])
                        cursor.execute(
                            "INSERT INTO marketing_trends (timestamp, keyword, interest) VALUES (?, ?, ?)",
                            (timestamp, kw, interest_val)
                        )
                    except Exception as e:
                        log.error(f"[MARKETING AGENT] Error saving data for {kw} at {timestamp}: {e}")
            conn.commit()
            conn.close()
            log.info("[MARKETING AGENT] Trends saved to database.")
        except Exception as e:
            log.error(f"[MARKETING AGENT] Error saving to DB: {e}")

    def run(self):
        """
        Execute the full marketing trends analysis pipeline.
        """
        try:
            log.info("[MARKETING AGENT] Fetching marketing trend data...")
            trends_df = self.fetch_trends()
            if trends_df.empty:
                log.warning("[MARKETING AGENT] No trends fetched. Aborting run.")
                return
            analysis = self.analyze_trends(trends_df)
            self.save_to_db(trends_df)
            log.info("[MARKETING AGENT] Run complete. Analysis summary: {}".format(analysis))
        except Exception as e:
            log.error(f"[MARKETING AGENT] Error during run: {e}")

