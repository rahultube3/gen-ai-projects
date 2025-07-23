#!/usr/bin/env python3
import sys
import signal
import asyncio
from weather import mcp

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutting down MCP weather server...")
    sys.exit(0)

def main():
    """Run the MCP weather server."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("Starting MCP weather server...")
        mcp.run()
    except OSError as e:
        if "Address already in use" in str(e) or "PORT IS IN USE" in str(e):
            print(f"Error: Port is already in use. {e}")
            print("Try stopping any existing MCP servers or wait a moment before retrying.")
            sys.exit(1)
        else:
            raise
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
