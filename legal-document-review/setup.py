#!/usr/bin/env python3
"""
Setup script for Legal Document Review RAG System
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command with error handling."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_mongodb():
    """Check if MongoDB is accessible."""
    try:
        import pymongo
        # Try to connect with default local settings
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        client.close()
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"⚠️  MongoDB not accessible: {str(e)}")
        print("   Please ensure MongoDB is running or update MONGO_DB_URI in .env")
        return False

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path(".env")
    example_file = Path(".env.example")
    
    if not env_file.exists() and example_file.exists():
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from .env.example")
        print("   Please update MONGO_DB_URI in .env file")
        return True
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("⚠️  .env.example not found, creating basic .env file")
        with open(".env", "w") as f:
            f.write("MONGO_DB_URI=mongodb://localhost:27017\n")
            f.write("LOG_LEVEL=INFO\n")
        return True

def main():
    """Main setup function."""
    print("🏛️  Legal Document Review RAG System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("⚠️  Dependency installation failed. You may need to install manually.")
    
    # Create .env file
    create_env_file()
    
    # Check MongoDB connection
    check_mongodb()
    
    print("\n🎯 Setup Summary:")
    print("1. Dependencies installed")
    print("2. Environment file created")
    print("3. MongoDB connection tested")
    print("\n📋 Next Steps:")
    print("1. Update .env file with your MongoDB connection string")
    print("2. Run: python db_setup.py")
    print("3. Run: python main.py")
    print("\n✨ Setup completed!")

if __name__ == "__main__":
    main()
