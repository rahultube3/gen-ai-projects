from typing import Any, List, Dict
import sys
import httpx
from mcp.server.fastmcp import FastMCP
import logging

logging.basicConfig(level=logging.INFO)
# Initialize FastMCP server with a specific port to avoid conflicts
mcp = FastMCP("weather1")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
NUM_FORECAST_PERIODS = 5  # Number of forecast periods to show

# Sample data for resources
AVAILABLE_RESOURCES = [
    {
        "uri": "weather://reports/san-francisco",
        "name": "San Francisco Weather Report",
        "description": "Cached weather report for San Francisco",
        "mimeType": "text/plain"
    },
    {
        "uri": "weather://reports/new-york", 
        "name": "New York Weather Report",
        "description": "Cached weather report for New York",
        "mimeType": "text/plain"
    },
    {
        "uri": "weather://reports/chicago",
        "name": "Chicago Weather Report", 
        "description": "Cached weather report for Chicago",
        "mimeType": "text/plain"
    },
    {
        "uri": "weather://alerts/ca",
        "name": "California Weather Alerts",
        "description": "Current weather alerts for California",
        "mimeType": "text/plain"
    },
    {
        "uri": "weather://alerts/ny",
        "name": "New York Weather Alerts",
        "description": "Current weather alerts for New York", 
        "mimeType": "text/plain"
    },
    {
        "uri": "weather://alerts/fl",
        "name": "Florida Weather Alerts",
        "description": "Current weather alerts for Florida",
        "mimeType": "text/plain"
    },
    {
        "uri": "weather://alerts/tx",
        "name": "Texas Weather Alerts",
        "description": "Current weather alerts for Texas",
        "mimeType": "text/plain"
    },
    {
        "uri": "weather://alerts/il",
        "name": "Illinois Weather Alerts", 
        "description": "Current weather alerts for Illinois",
        "mimeType": "text/plain"
    }
]

# Note: Resources are defined using @mcp.resource() decorators below
# FastMCP will automatically discover them

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logging.error(f"Error making NWS request to {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error in NWS request: {e}")
        return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""
@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    try:
        url = f"{NWS_API_BASE}/alerts/active/area/{state}"
        data = await make_nws_request(url)

        if not data or "features" not in data:
            return "Unable to fetch alerts or no alerts found."

        if not data["features"]:
            return "No active alerts for this state."

        alerts = [format_alert(feature) for feature in data["features"]]
        return "\n---\n".join(alerts)
    except Exception as e:
        return f"Error fetching alerts: {str(e)}"

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    try:
        # First get the forecast grid endpoint
        points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
        points_data = await make_nws_request(points_url)

        if not points_data:
            return "Unable to fetch forecast data for this location."

        # Get the forecast URL from the points response
        properties = points_data.get("properties", {})
        forecast_url = properties.get("forecast")
        if not forecast_url:
            return "Forecast URL not found in the API response."

        forecast_data = await make_nws_request(forecast_url)
        if not forecast_data:
            return "Unable to fetch forecast details from the API."
        
        # Format the periods into a readable forecast
        properties = forecast_data.get("properties", {})
        periods = properties.get("periods")
        if not periods:
            return "No forecast periods found in the API response."
        
        forecasts = []
        for period in periods[:NUM_FORECAST_PERIODS]:  # Only show next NUM_FORECAST_PERIODS periods
            forecast = f"""
{period.get('name', 'Unknown')}:
Temperature: {period.get('temperature', 'N/A')}°{period.get('temperatureUnit', '')}
Wind: {period.get('windSpeed', 'N/A')} {period.get('windDirection', '')}
Forecast: {period.get('detailedForecast', 'No forecast available')}
"""
            forecasts.append(forecast)

        return "\n---\n".join(forecasts)
    except Exception as e:
        return f"Error fetching forecast: {str(e)}"

@mcp.resource("weather://reports/{location}")
def get_weather_report(location: str) -> str:
    """Get a cached weather report for a location."""
    # This simulates a cached weather report resource
    # In a real implementation, this could read from a local cache or database
    sample_reports = {
        "san-francisco": """
# Weather Report: San Francisco, CA
Last Updated: July 23, 2025

## Current Conditions
- Temperature: 66°F
- Conditions: Partly Cloudy
- Humidity: 78%
- Wind: 12 mph W

## Recent Alerts
- Coastal Flood Advisory (Minor)
- High Wind Watch

## 7-Day Outlook
Mostly mild temperatures with typical marine layer influence.
""",
        "new-york": """
# Weather Report: New York, NY
Last Updated: July 23, 2025

## Current Conditions
- Temperature: 82°F
- Conditions: Sunny
- Humidity: 65%
- Wind: 8 mph SW

## Recent Alerts
- Heat Advisory

## 7-Day Outlook
Hot and humid conditions expected to continue.
""",
        "chicago": """
# Weather Report: Chicago, IL
Last Updated: July 23, 2025

## Current Conditions
- Temperature: 75°F
- Conditions: Partly Cloudy
- Humidity: 72%
- Wind: 10 mph NW

## Recent Alerts
- None

## 7-Day Outlook
Pleasant summer weather with occasional showers.
"""
    }
    
    location_key = location.lower().replace(" ", "-").replace(",", "")
    
    if location_key in sample_reports:
        return sample_reports[location_key]
    else:
        return f"""
# Weather Report: {location}
Last Updated: July 23, 2025

## Status
No cached weather report available for this location.
Please use the get_forecast tool for live weather data.

## Available Cached Locations
- san-francisco
- new-york  
- chicago

## Suggestion
Try: weather://reports/san-francisco
"""

@mcp.resource("weather://alerts/{state}")
def get_alert_summary(state: str) -> str:
    """Get a summary of weather alerts for a state."""
    # This simulates a cached alert summary resource
    state_info = {
        "ca": "California - Known for wildfire, earthquake, and coastal flood risks",
        "ny": "New York - Prone to winter storms, hurricanes, and heat waves", 
        "fl": "Florida - Hurricane season, thunderstorms, and heat advisories",
        "tx": "Texas - Severe thunderstorms, tornadoes, and extreme heat",
        "il": "Illinois - Severe weather, winter storms, and flooding"
    }
    
    state_key = state.lower()
    info = state_info.get(state_key, f"{state.upper()} - Use get_alerts tool for current conditions")
    
    return f"""
# Weather Alert Summary: {state.upper()}

## State Profile
{info}

## Resource Information
This is a cached summary. For real-time alerts, use the get_alerts tool.

## Usage
- Current alerts: Use get_alerts("{state.upper()}")
- Forecast data: Use get_forecast(latitude, longitude)

Last updated: July 23, 2025
"""

@mcp.prompt("weather-alert-analysis")
def prompt_weather_alerts() -> str:
    """Generate a prompt for analyzing weather alerts and conditions."""
    return """You are a weather expert assistant with access to real-time weather data through the National Weather Service API. You can help users understand weather alerts, forecast conditions, and provide safety recommendations.

Available tools:
- get_alerts(state): Get active weather alerts for any US state (use 2-letter state codes like CA, NY, TX)
- get_forecast(latitude, longitude): Get detailed weather forecasts for specific coordinates

Available resources:
- weather://reports/{location}: Cached weather reports for major cities (san-francisco, new-york, chicago)
- weather://alerts/{state}: State weather risk profiles and guidance

When responding to weather queries:
1. Use get_alerts() to check for active warnings, watches, or advisories
2. Use get_forecast() for detailed conditions and upcoming weather
3. Explain the significance of any alerts (what they mean, safety precautions)
4. Provide context about typical weather patterns for the region
5. Suggest appropriate actions based on the weather conditions

Example queries you can help with:
- "What are the current weather alerts for California?"
- "What's the forecast for San Francisco this week?"
- "Are there any severe weather warnings in Texas?"
- "Should I be concerned about the weather in New York today?"

Remember to prioritize safety and provide clear, actionable weather information."""

@mcp.prompt("weather-safety-guide") 
def prompt_weather_safety() -> str:
    """Generate a prompt for weather safety guidance."""
    return """You are a weather safety expert helping people understand and prepare for various weather conditions. Use the available weather tools to provide current conditions and combine that with safety expertise.

Focus areas:
1. **Alert Interpretation**: Explain what different weather alerts mean (watches vs warnings vs advisories)
2. **Safety Protocols**: Provide specific actions for different weather events
3. **Preparation**: Help users prepare for incoming weather
4. **Risk Assessment**: Evaluate weather risks for planned activities

Weather Alert Severity Levels:
- **Advisory**: Be aware, minor inconvenience expected
- **Watch**: Conditions are favorable for severe weather
- **Warning**: Severe weather is occurring or imminent

Safety priorities by weather type:
- **Severe Thunderstorms**: Seek shelter indoors, avoid windows
- **Tornadoes**: Go to lowest floor, interior room, cover yourself
- **Flash Floods**: Never drive through flooded roads, seek higher ground
- **Heat**: Stay hydrated, limit outdoor activities, seek air conditioning
- **Winter Storms**: Avoid travel, prepare for power outages

Always check current alerts and forecasts before providing advice, and emphasize that when in doubt, people should follow local emergency management guidance."""
