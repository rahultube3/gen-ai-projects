from typing import Optional
import httpx
from dotenv import load_dotenv
import os
import logging
import asyncio
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("TradingAlerts")
# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables (API Key)
load_dotenv()
BENZINGA_API_KEY = os.getenv("BENZINGA_API_KEY")
BENZINGA_API_URL = os.getenv("BENZINGA_API_URL")

async def fetch_trading_news(api_key: str) -> Optional[dict]:
    """Fetch trading news for a given symbol using Benzinga API."""
    
    headers = {"accept": "application/json"}
    params = {
        "token": api_key,
            "displayOutput": "headlines",
            "displayType": "json",
            "sortBy": "created"
        }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BENZINGA_API_URL, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logging.error(f"Error fetching news: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error {e.response.status_code}: {e}")
            return None

@mcp.tool()
async def get_trading_news(symbol: str = "AAPL", limit: int = 10) -> str:
    """Get latest trading news for a stock symbol.

    Args:
        symbol: Stock symbol (e.g. AAPL, TSLA, MSFT)
        limit: Number of news articles to return (default 10)
    """
    if not BENZINGA_API_KEY:
        return "Error: BENZINGA_API_KEY not set in environment variables."
    
    try:
        news_data = await fetch_trading_news(BENZINGA_API_KEY)
        
        if not news_data:
            return f"Unable to fetch news for {symbol}. Please check the symbol and try again."
        
        # Handle different response formats
        articles = []
        if isinstance(news_data, dict):
            articles = news_data.get('data', [])
        elif isinstance(news_data, list):
            articles = news_data
        else:
            return f"Unexpected response format from news API: {type(news_data)}"
        
        if not articles:
            return f"No recent news found for {symbol}."
        
        # Format the news articles
        news_items = []
        for i, article in enumerate(articles[:limit]):
            title = article.get('title', 'No title')
            summary = article.get('teaser', article.get('summary', 'No summary available'))
            published = article.get('created', article.get('published', 'Unknown date'))
            url = article.get('url', 'No URL')
            
            news_item = f"""
Article {i+1}:
Title: {title}
Summary: {summary}
Published: {published}
URL: {url}
"""
            news_items.append(news_item.strip())
        
        result = f"Latest {len(news_items)} trading news articles:\n\n"
        result += "\n\n---\n\n".join(news_items)
        
        return result
        
    except Exception as e:
        return f"Error fetching trading news: {str(e)}"