#!/usr/bin/env python3
"""
MCP Trading Alerts Server
A Model Context Protocol server for trading news and alerts using Benzinga API.
"""

from typing import Any, Dict, List
import sys
import httpx
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("trading-alerts")

# Constants
BENZINGA_API_KEY = os.getenv("BENZINGA_API_KEY")
BENZINGA_API_URL = os.getenv("BENZINGA_API_URL", "https://api.benzinga.com/api/v2/news")
USER_AGENT = "trading-alerts-mcp/1.0"

async def make_benzinga_request(url: str, params: dict = None) -> dict[str, Any] | None:
    """Make a request to the Benzinga API with proper error handling."""
    if not BENZINGA_API_KEY:
        print("Error: BENZINGA_API_KEY not set", file=sys.stderr)
        return None
        
    headers = {
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, params=params or {})
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        print(f"Timeout error: Request to {url} timed out", file=sys.stderr)
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error {e.response.status_code}: {e.response.text}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        return None

@mcp.tool()
async def get_trading_news(symbol: str, limit: int = 5) -> str:
    """Get latest trading news for a stock symbol.

    Args:
        symbol: Stock symbol (e.g. AAPL, TSLA, MSFT)
        limit: Number of news articles to return (default 5, max 50)
    """
    try:
        limit = max(1, min(limit, 50))  # Ensure limit is between 1 and 50
        
        params = {
            "tickers": symbol.upper(),
            "pagesize": limit,
            "displayOutput": "full",
            "token": BENZINGA_API_KEY,
        }
        
        news_data = await make_benzinga_request(BENZINGA_API_URL, params)
        
        if not news_data:
            return f"Unable to fetch news for {symbol}. Please check the symbol and try again."
        
        articles = news_data.get("data", [])
        
        if not articles:
            return f"No recent news found for {symbol}."
        
        # Format the news articles
        news_items = []
        for article in articles[:limit]:
            title = article.get("title", "No title")
            summary = article.get("teaser", "No summary available")
            published = article.get("created", "Unknown date")
            url = article.get("url", "No URL")
            
            news_item = f"""
Title: {title}
Summary: {summary}
Published: {published}
URL: {url}
"""
            news_items.append(news_item.strip())
        
        result = f"Latest {len(news_items)} news articles for {symbol.upper()}:\n\n"
        result += "\n\n---\n\n".join(news_items)
        
        return result
        
    except Exception as e:
        return f"Error fetching news for {symbol}: {str(e)}"

@mcp.tool()
async def get_market_movers(direction: str = "up") -> str:
    """Get top market movers (gainers or losers).

    Args:
        direction: Either 'up' for gainers or 'down' for losers
    """
    try:
        # This would typically use a different endpoint
        # For now, we'll return a mock response since Benzinga's movers endpoint may differ
        direction = direction.lower()
        if direction not in ["up", "down"]:
            return "Direction must be either 'up' or 'down'"
            
        # Mock response - in a real implementation, you'd use the appropriate Benzinga endpoint
        movers_type = "gainers" if direction == "up" else "losers"
        
        return f"""Market {movers_type} information would be available here.
        
To implement this feature, you would need to:
1. Get access to Benzinga's market movers endpoint
2. Configure the appropriate API parameters
3. Parse and format the response

Current implementation is a placeholder."""
        
    except Exception as e:
        return f"Error fetching market movers: {str(e)}"

@mcp.resource("trading://news/{symbol}")
def get_cached_news(symbol: str) -> str:
    """Get cached trading news for a symbol."""
    # This simulates cached news - in a real implementation, 
    # this could read from a local cache or database
    sample_news = {
        "aapl": """
# Trading News: Apple Inc. (AAPL)
Last Updated: July 23, 2025

## Recent Headlines
- Apple Reports Strong Q3 Earnings Beat
- iPhone Sales Exceed Expectations in Global Markets  
- Apple Announces New AI Features for iOS 19
- Services Revenue Continues Growth Trajectory

## Key Metrics
- Stock Price: $195.50 (+2.5%)
- Market Cap: $3.1T
- P/E Ratio: 29.2
- 52-Week Range: $164.08 - $199.62
""",
        "tsla": """
# Trading News: Tesla Inc. (TSLA)
Last Updated: July 23, 2025

## Recent Headlines
- Tesla Delivers Record Vehicle Numbers in Q2
- Cybertruck Production Ramps Up Ahead of Schedule
- Supercharger Network Expansion Accelerates
- Energy Storage Business Shows Strong Growth

## Key Metrics
- Stock Price: $248.75 (+1.8%)
- Market Cap: $790B
- P/E Ratio: 52.1
- 52-Week Range: $138.80 - $278.98
""",
        "msft": """
# Trading News: Microsoft Corp. (MSFT)
Last Updated: July 23, 2025

## Recent Headlines
- Azure Cloud Services Revenue Grows 31% YoY
- Microsoft Copilot Adoption Surpasses Expectations
- Enterprise Software Division Reports Record Quarter
- AI Integration Drives Office 365 Growth

## Key Metrics
- Stock Price: $425.30 (+1.2%)
- Market Cap: $3.2T
- P/E Ratio: 34.7
- 52-Week Range: $309.45 - $449.85
"""
    }
    
    symbol_lower = symbol.lower()
    if symbol_lower in sample_news:
        return sample_news[symbol_lower]
    else:
        return f"""
# Trading News: {symbol.upper()}
Last Updated: July 23, 2025

## Information
No cached news available for {symbol.upper()}.
Use the get_trading_news tool to fetch live news data.

## Available Cached Symbols
- AAPL (Apple Inc.)
- TSLA (Tesla Inc.)
- MSFT (Microsoft Corp.)
"""

@mcp.resource("trading://alerts/{symbol}")
def get_trading_alerts(symbol: str) -> str:
    """Get trading alerts and watchlist information for a symbol."""
    # This simulates trading alerts - in a real implementation,
    # this could include price alerts, volume alerts, etc.
    alerts_data = {
        "aapl": """
# Trading Alerts: Apple Inc. (AAPL)

## Active Alerts
🔔 Price Alert: Above $195.00 (TRIGGERED)
🔔 Volume Alert: Above average volume detected
🔔 Earnings Alert: Next earnings date - Oct 26, 2025

## Technical Indicators
📈 RSI: 62.4 (Neutral)
📈 MACD: Bullish crossover
📈 Moving Averages: Above 50-day and 200-day MA

## Analyst Sentiment
👍 Buy: 28 analysts
👍 Hold: 8 analysts  
👍 Sell: 2 analysts
Average Price Target: $210.50
""",
        "tsla": """
# Trading Alerts: Tesla Inc. (TSLA)

## Active Alerts  
🔔 Price Alert: Below $250.00 (TRIGGERED)
🔔 News Alert: Production update announced
🔔 Options Alert: High put/call ratio detected

## Technical Indicators
📈 RSI: 45.2 (Neutral)
📈 MACD: Bearish divergence
📈 Moving Averages: Mixed signals

## Analyst Sentiment
👍 Buy: 18 analysts
👍 Hold: 12 analysts
👍 Sell: 8 analysts
Average Price Target: $275.00
"""
    }
    
    symbol_lower = symbol.lower()
    if symbol_lower in alerts_data:
        return alerts_data[symbol_lower]
    else:
        return f"""
# Trading Alerts: {symbol.upper()}

## No Active Alerts
No specific alerts configured for {symbol.upper()}.

## Available Alert Types
- Price alerts (above/below targets)
- Volume alerts (unusual activity)
- News alerts (breaking news)
- Earnings alerts (upcoming dates)
- Technical alerts (indicator signals)

Use the get_trading_news tool for live market data.
"""

@mcp.prompt("trading-analysis")
def trading_analysis_prompt() -> str:
    """Generate a prompt for trading analysis and decision making."""
    return """You are a professional trading analyst helping users make informed investment decisions. Use the available trading tools to provide current market data and combine that with analytical expertise.

Focus areas:
1. **Fundamental Analysis**: Examine company financials, earnings, and business outlook
2. **Technical Analysis**: Review chart patterns, indicators, and market trends  
3. **News Analysis**: Interpret how recent news might impact stock price
4. **Risk Assessment**: Identify potential risks and market volatility factors
5. **Market Context**: Consider broader market conditions and sector performance

When analyzing stocks:
- Always get current news and price data using available tools
- Provide both bullish and bearish perspectives
- Include specific price levels and timeframes
- Mention key catalysts and upcoming events
- Emphasize risk management and position sizing
- Remind users that past performance doesn't guarantee future results

Remember: This is educational analysis only, not financial advice. Users should conduct their own research and consult with financial advisors before making investment decisions."""

@mcp.prompt("risk-management")
def risk_management_prompt() -> str:
    """Generate a prompt for trading risk management guidance."""
    return """You are a risk management specialist helping traders and investors protect their capital. Use current market data to provide practical risk management strategies.

Key principles to emphasize:
1. **Position Sizing**: Never risk more than 1-2% of capital on a single trade
2. **Stop Losses**: Always define exit points before entering positions
3. **Diversification**: Spread risk across different assets and sectors
4. **Market Conditions**: Adjust strategy based on market volatility
5. **Emotional Control**: Avoid FOMO and panic-driven decisions

Risk assessment framework:
- Evaluate current market volatility using available tools
- Identify correlation risks in portfolio positions
- Monitor news events that could trigger market moves
- Consider economic calendar and earnings schedules
- Assess liquidity and trading volume

Provide specific, actionable advice on:
- Setting appropriate stop-loss levels
- Calculating position sizes based on account size
- Recognizing when to reduce position sizes
- Managing during high volatility periods
- Building emergency cash reserves

Always remind users that risk management is more important than profit maximization."""

if __name__ == "__main__":
    mcp.run()
