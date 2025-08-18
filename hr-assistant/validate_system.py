#!/usr/bin/env python3
"""
HR Assistant System Validation
Validates that all components can be imported and initialized correctly.
"""

import sys
import os
from pathlib import Path

def validate_environment():
    """Validate virtual environment and dependencies."""
    print("🔍 Validating HR Assistant System...")
    print("=" * 50)
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"✅ Python version: {python_version}")
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️  Not running in virtual environment")
    
    # Check core dependencies
    try:
        import fastapi
        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        print("❌ FastAPI not available")
        return False
    
    try:
        import openai
        print(f"✅ OpenAI: {openai.__version__}")
    except ImportError:
        print("❌ OpenAI not available")
        return False
    
    try:
        import pymongo
        print(f"✅ PyMongo: {pymongo.__version__}")
    except ImportError:
        print("❌ PyMongo not available")
        return False
    
    try:
        import streamlit
        print(f"✅ Streamlit: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not available")
        return False
    
    # Check file structure
    required_files = [
        "rag_system.py",
        "comprehensive_api.py", 
        "simple_chat.py",
        "ingest_mongodb.py",
        "requirements_basic.txt"
    ]
    
    print("\n📁 Checking file structure...")
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} missing")
            return False
    
    # Check startup scripts
    startup_scripts = [
        "start_all.sh",
        "start_rag.sh", 
        "start_comprehensive.sh",
        "start_streamlit.sh"
    ]
    
    print("\n🚀 Checking startup scripts...")
    for script in startup_scripts:
        script_path = Path(script)
        if script_path.exists():
            if os.access(script_path, os.X_OK):
                print(f"✅ {script} (executable)")
            else:
                print(f"⚠️  {script} (not executable)")
        else:
            print(f"❌ {script} missing")
            return False
    
    # Check environment file
    if Path(".env").exists():
        print("✅ .env file exists")
        
        # Basic env validation
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            mongo_uri = os.getenv("MONGO_DB_URI")
            openai_key = os.getenv("OPENAI_API_KEY")
            
            if mongo_uri:
                print("✅ MONGO_DB_URI configured")
            else:
                print("⚠️  MONGO_DB_URI not set")
            
            if openai_key:
                print("✅ OPENAI_API_KEY configured")
            else:
                print("⚠️  OPENAI_API_KEY not set")
                
        except ImportError:
            print("⚠️  python-dotenv not available for env validation")
    else:
        print("⚠️  .env file missing")
    
    print("\n🎉 System validation complete!")
    print("\nTo start the complete system, run:")
    print("./start_all.sh")
    print("\nOr start components individually:")
    print("./start_rag.sh")
    print("./start_comprehensive.sh") 
    print("./start_streamlit.sh")
    
    return True

if __name__ == "__main__":
    validate_environment()
