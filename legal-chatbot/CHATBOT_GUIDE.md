# Legal Document Chatbot - Quick Start Guide

This directory contains simple scripts to quickly start your Legal Document Chatbot system.

**Note:** Run these scripts from the `legal-chatbot/` directory.

## 🚀 Quick Start

Navigate to the legal-chatbot directory first:
```bash
cd legal-chatbot/
```

Then run either script:

### Option 1: Bash Script (Recommended)
```bash
./run_chatbot.sh
```

### Option 2: Python Script
```bash
python3 run_chatbot.py
```

## 📋 What These Scripts Do

Both scripts will automatically:

1. **🔧 Setup Backend API**
   - Navigate to `../legal-document-review/` directory
   - Create Python virtual environment (if needed)
   - Install Python dependencies
   - Start FastAPI server on port 8000

2. **🔧 Setup Frontend**
   - Use current `legal-chatbot/` directory
   - Install Node.js dependencies (if needed)
   - Start Angular development server on port 4200

3. **🎯 Launch Services**
   - Backend API: http://localhost:8000
   - Frontend Chat: http://localhost:4200
   - API Documentation: http://localhost:8000/docs

## 🛑 Stopping the Services

Press `Ctrl+C` in the terminal to stop all services. The scripts will automatically clean up background processes.

## 📁 Project Structure

```
gen-ai-projects/
├── legal-document-review/     # Backend RAG API
└── legal-chatbot/            # Angular Frontend
    ├── src/                  # Angular source code
    ├── run_chatbot.sh        # Bash startup script
    ├── run_chatbot.py        # Python startup script
    └── CHATBOT_GUIDE.md      # This file
```

## 🔧 Manual Setup (Alternative)

If you prefer to start services manually:

### Backend:
```bash
cd ../legal-document-review/
source venv/bin/activate
pip install -r requirements.txt
python api_server.py
```

### Frontend:
```bash
# Already in legal-chatbot directory
npm install
npm start
```

## 🐛 Troubleshooting

### Port Already in Use
If you get port errors, check what's running:
```bash
# Check port 8000 (backend)
lsof -i :8000

# Check port 4200 (frontend)  
lsof -i :4200

# Kill processes if needed
kill -9 <PID>
```

### Dependencies Issues
- **Backend**: Make sure Python 3.8+ is installed
- **Frontend**: Make sure Node.js 18+ and npm are installed

### Permission Issues
Make scripts executable:
```bash
chmod +x run_chatbot.sh
chmod +x run_chatbot.py
```

## 🎯 Usage Tips

1. **First Time Setup**: Scripts will automatically install dependencies
2. **Startup Time**: Angular build takes 30-60 seconds on first run - be patient!
3. **Development**: Leave services running and make code changes - they'll auto-reload
4. **Testing**: Use the API docs at http://localhost:8000/docs to test backend endpoints
5. **Chat Interface**: Access the full chat UI at http://localhost:4200
6. **Running Location**: Always run these scripts from within the `legal-chatbot/` directory

## 🔗 Service URLs

- **Chat Interface**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

Enjoy your Legal Document Chatbot! 🎉
