# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather forecasting and alerts using the National Weather Service API.

## Features

- Get weather forecasts for any US location using latitude/longitude
- Get active weather alerts for US states
- Built with FastMCP for easy integration
- **Complete MCP Implementation**: Tools, Resources, and Prompts
- Real-time data from National Weather Service API
- Cached weather reports and state profiles
- AI assistant prompts for weather analysis and safety

## MCP Implementation Overview

This weather server demonstrates all three core MCP capabilities:

### 🛠️ **Tools** (Dynamic Functions)
- Live weather data from external APIs
- Async functions with real-time results
- `get_alerts()` and `get_forecast()`

### 📚 **Resources** (Static Content)  
- Structured, cacheable content with URIs
- Pre-formatted weather reports and guides
- `weather://reports/*` and `weather://alerts/*`

### 💭 **Prompts** (AI Instructions)
- System prompts for AI assistants
- Weather expertise and safety guidance
- `weather-alert-analysis` and `weather-safety-guide`

## Setup

### 1. Install Dependencies

The MCP package with CLI tools is already installed via:
```bash
uv add "mcp[cli]"
```

### 2. Configure Claude Desktop

To use this MCP server with Claude Desktop, you need to add the server configuration to Claude's config file.

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "weather": {
      "command": "uv",
      "args": ["run", "python", "~/gen-ai-projects/mcp-weather-server/main.py"],
      "env": {}
    }
  }
}
```

**Important**: Update the path in the `args` array to match your actual project location.

### 3. Run the Server

You can test the server locally:

```bash
cd mcp-weather-server
python main.py
```

### 3a. Run with MCP Inspector (Recommended for Testing)

The MCP Inspector provides a web interface to test your MCP server:

```bash
cd mcp-weather-server
./manage_server.sh inspector
```

This will:
- Start the MCP weather server
- Launch the MCP Inspector web interface at http://localhost:6274
- Display a session token for authentication
- Allow you to test the server's tools interactively

**Note**: If you see an authentication error in the inspector, either:
1. Use the displayed session token to authenticate
2. Set `DANGEROUSLY_OMIT_AUTH=true` environment variable to disable auth for testing

### 4. Restart Claude Desktop

After adding the configuration, restart Claude Desktop completely for the changes to take effect.

## Usage

Once configured, you can ask Claude to:

- Get weather forecasts: "What's the weather forecast for San Francisco?" (Claude will ask for coordinates)
- Get weather alerts: "Are there any weather alerts for California?"

## Tools Available

- `get_forecast(latitude: float, longitude: float)` - Get weather forecast for coordinates
- `get_alerts(state: str)` - Get active weather alerts for a US state (2-letter code)

## Resources Available

### Weather Reports
- **URI Pattern**: `weather://reports/{location}`
- **Purpose**: Cached weather reports for major cities
- **Available Locations**:
  - `weather://reports/san-francisco`
  - `weather://reports/new-york`
  - `weather://reports/chicago`

### Weather Alert Summaries
- **URI Pattern**: `weather://alerts/{state}`
- **Purpose**: State weather profiles and alert guidance
- **Available States**: 
  - `weather://alerts/ca` (California)
  - `weather://alerts/ny` (New York)
  - `weather://alerts/fl` (Florida)
  - `weather://alerts/tx` (Texas)
  - `weather://alerts/il` (Illinois)

## Prompts Available

### Weather Alert Analysis
- **Prompt ID**: `weather-alert-analysis`
- **Purpose**: Provides AI assistant instructions for analyzing weather alerts and conditions
- **Features**: Explains tools, resources, alert interpretation, and safety recommendations

### Weather Safety Guide  
- **Prompt ID**: `weather-safety-guide`
- **Purpose**: Provides AI assistant instructions for weather safety guidance
- **Features**: Alert severity levels, safety protocols, preparation guidance, and risk assessment

## Troubleshooting

### Connection Error - Proxy Session Token

If you see this error, it usually means:

1. The MCP server configuration is not properly added to Claude Desktop's config file
2. The path to your server is incorrect in the configuration
3. Claude Desktop hasn't been restarted after configuration changes
4. The server script has errors preventing it from starting

### Port In Use Error

If you see "Proxy Server PORT IS IN USE at port 6277", it means another instance of the MCP server is already running. To fix this:

**Option 1: Use the management script**
```bash
./manage_server.sh stop     # Stop any running server
./manage_server.sh start    # Start the server
./manage_server.sh restart  # Restart the server
./manage_server.sh status   # Check server status
./manage_server.sh cleanup  # Clean up stuck processes
```

**Option 2: Manual cleanup**
```bash
# Find processes using port 6277
lsof -ti:6277

# Kill the processes (replace with actual PIDs)
kill -9 <PID1> <PID2>

# Or kill all related processes
pkill -f "mcp-weather-server"
```

### Steps to Fix Connection Issues

1. Verify the config file location for your OS
2. Double-check the path to main.py in the configuration
3. Test the server runs locally without errors: `./manage_server.sh test`
4. Completely restart Claude Desktop (quit and reopen)
5. Check Claude Desktop's logs if available

### Recent Fixes

**Fixed "object dict can't be used in 'await' expression" Error (July 22, 2025)**
- Fixed duplicate line in `get_forecast` function
- Improved error handling in both `get_alerts` and `get_forecast`
- Added proper async/await error handling
- Added comprehensive logging for debugging
- All functions now work correctly as verified by test suite

## Testing

You can test the MCP server directly using the MCP CLI tools:

```bash
# Install MCP CLI if not already available
mcp --help

# Test the server (adjust path as needed)
mcp run /path/to/your/main.py
```
