#!/usr/bin/env python3
"""
Legal Chatbot Startup Script (Python Version)
This script starts both the backend RAG API and the Angular frontend
"""

import subprocess
import time
import signal
import sys
import os
import socket
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class ChatbotLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.root_dir = Path(__file__).parent
        
    def print_colored(self, message, color=Colors.NC):
        print(f"{color}{message}{Colors.NC}")
        
    def check_port(self, port):
        """Check if a port is in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            return result == 0
            
    def wait_for_service(self, port, service_name, max_attempts=60):
        """Wait for a service to start on the specified port"""
        self.print_colored(f"Waiting for {service_name} to start on port {port}...", Colors.YELLOW)
        
        for attempt in range(1, max_attempts + 1):
            # Check if the process is still running (for frontend)
            if service_name == "Frontend Server" and self.frontend_process:
                if self.frontend_process.poll() is not None:
                    self.print_colored("❌ Angular process has exited unexpectedly", Colors.RED)
                    return False
            
            if self.check_port(port):
                self.print_colored(f"✅ {service_name} is running on port {port}", Colors.GREEN)
                return True
            
            # Show progress every 5 attempts for frontend (which takes longer)
            if service_name == "Frontend Server" and attempt % 5 == 0:
                self.print_colored(f"⏳ Attempt {attempt}/{max_attempts} - Angular is building, please wait...", Colors.YELLOW)
            elif service_name != "Frontend Server":
                self.print_colored(f"Attempt {attempt}/{max_attempts} - waiting for {service_name}...", Colors.YELLOW)
            
            time.sleep(3)  # Increased wait time for better stability
            
        self.print_colored(f"❌ Failed to start {service_name} on port {port}", Colors.RED)
        return False
        
    def cleanup(self, signum=None, frame=None):
        """Cleanup background processes"""
        self.print_colored("\n🛑 Shutting down services...", Colors.YELLOW)
        
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
            self.print_colored("✅ Backend API stopped", Colors.GREEN)
            
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process.wait()
            self.print_colored("✅ Frontend server stopped", Colors.GREEN)
            
        # Kill any remaining processes
        try:
            subprocess.run(["pkill", "-f", "uvicorn.*api_server:app"], capture_output=True)
            subprocess.run(["pkill", "-f", "ng serve"], capture_output=True)
        except:
            pass
            
        self.print_colored("🎉 All services stopped successfully", Colors.GREEN)
        sys.exit(0)
        
    def start_backend(self):
        """Start the backend API server"""
        self.print_colored("🔧 Starting Backend API...", Colors.BLUE)
        
        backend_dir = self.root_dir.parent / "legal-document-review"
        if not backend_dir.exists():
            self.print_colored("❌ Backend directory 'legal-document-review' not found", Colors.RED)
            return False
            
        # Change to backend directory
        os.chdir(backend_dir)
        
        # Check if virtual environment exists
        venv_dir = backend_dir / "venv"
        if not venv_dir.exists():
            self.print_colored("📦 Creating Python virtual environment...", Colors.YELLOW)
            subprocess.run([sys.executable, "-m", "venv", "venv"])
            
        # Install dependencies
        pip_path = venv_dir / "bin" / "pip"
        subprocess.run([str(pip_path), "install", "-q", "-r", "requirements.txt"])
        
        # Start the backend API
        self.print_colored("🚀 Launching FastAPI server...", Colors.BLUE)
        python_path = venv_dir / "bin" / "python"
        self.backend_process = subprocess.Popen([str(python_path), "api_server.py"])
        
        # Wait for backend to start
        if not self.wait_for_service(8000, "Backend API"):
            self.print_colored("❌ Failed to start backend API", Colors.RED)
            return False
            
        return True
        
    def start_frontend(self):
        """Start the Angular frontend server"""
        self.print_colored("🔧 Starting Frontend...", Colors.BLUE)
        
        frontend_dir = self.root_dir
        if not frontend_dir.exists():
            self.print_colored("❌ Frontend directory 'legal-chatbot' not found", Colors.RED)
            return False
            
        # Change to frontend directory
        os.chdir(frontend_dir)
        
        # Install dependencies if needed
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            self.print_colored("📦 Installing Node.js dependencies...", Colors.YELLOW)
            subprocess.run(["npm", "install"])
            
        # Start the Angular development server
        self.print_colored("🚀 Launching Angular development server...", Colors.BLUE)
        ng_path = frontend_dir / "node_modules" / "@angular" / "cli" / "bin" / "ng.js"
        
        # Use npm start instead of direct ng serve for better compatibility
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "start"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(frontend_dir)
            )
            self.print_colored("📝 Angular server starting in background...", Colors.YELLOW)
            self.print_colored("⏳ First build may take 30-60 seconds, please be patient", Colors.BLUE)
        except Exception as e:
            self.print_colored(f"❌ Failed to start Angular server: {e}", Colors.RED)
            return False
        
        # Wait for frontend to start
        if not self.wait_for_service(4200, "Frontend Server"):
            # If it failed, check if the process is still running
            if self.frontend_process and self.frontend_process.poll() is not None:
                stdout, stderr = self.frontend_process.communicate()
                self.print_colored("❌ Angular process exited with errors:", Colors.RED)
                if stderr:
                    self.print_colored(f"Error: {stderr.decode()}", Colors.RED)
                if stdout:
                    self.print_colored(f"Output: {stdout.decode()}", Colors.YELLOW)
            self.print_colored("❌ Failed to start frontend server", Colors.RED)
            return False
            
        return True
        
    def run(self):
        """Main execution function"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        self.print_colored("🚀 Starting Legal Document Chatbot...", Colors.GREEN)
        self.print_colored("==================================", Colors.GREEN)
        
        # Start backend
        if not self.start_backend():
            sys.exit(1)
            
        # Start frontend  
        if not self.start_frontend():
            sys.exit(1)
            
        # Success message
        self.print_colored("\n🎉 Legal Document Chatbot is now running!", Colors.GREEN)
        self.print_colored("=================================", Colors.GREEN)
        self.print_colored("📱 Frontend (Angular): http://localhost:4200", Colors.BLUE)
        self.print_colored("🔧 Backend API: http://localhost:8000", Colors.BLUE)
        self.print_colored("📚 API Documentation: http://localhost:8000/docs", Colors.BLUE)
        self.print_colored("\nPress Ctrl+C to stop all services", Colors.YELLOW)
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.cleanup()

if __name__ == "__main__":
    launcher = ChatbotLauncher()
    launcher.run()
