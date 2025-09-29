#!/usr/bin/env python3
"""
Simple HTTP server to serve the AngularJS chatbot frontend
"""
import http.server
import socketserver
import os
import sys
from pathlib import Path

def serve_frontend(port=3000, directory=None):
    """Serve the frontend directory"""
    if directory is None:
        directory = Path(__file__).parent / "chatbot-frontend"
    
    # Change to the frontend directory
    os.chdir(directory)
    
    # Create server
    handler = http.server.SimpleHTTPRequestHandler
    
    # Add CORS headers
    class CORSRequestHandler(handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    with socketserver.TCPServer(("", port), CORSRequestHandler) as httpd:
        print(f"🌐 Serving AngularJS frontend at http://localhost:{port}")
        print(f"📁 Directory: {directory}")
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Frontend server stopped")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    serve_frontend(port)