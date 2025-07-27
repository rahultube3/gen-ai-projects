#!/usr/bin/env python3
import sys
import signal
import asyncio
from trading_server import mcp

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutting down MCP trading alerts server...")
    sys.exit(0)

def main():
    """Run the MCP trading alerts server."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("Starting MCP trading alerts server...")
        mcp.run()
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
