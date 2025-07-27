# Banking Fraud Detection MCP Server - Complete Project

## 🏦 Project Overview

A comprehensive, production-ready Model Context Protocol (MCP) server for banking fraud detection with DuckDB backend, multiple client interfaces, and Docker deployment support.

## 🎯 Features

### Core MCP Server
- **3 Tools**: `check_fraud`, `get_fraud_statistics`, `analyze_customer_risk`
- **3 Resources**: System status, risk patterns, sample transactions
- **2 Prompts**: Fraud analysis and security advisory templates
- **FastMCP Framework**: High-performance, async MCP implementation

### Database & Data
- **DuckDB Backend**: Lightweight, high-performance SQL database
- **Sample Data**: 5 customers, 8 transactions with realistic fraud scenarios
- **Dynamic Risk Scoring**: Real-time fraud probability calculations

### Client Interfaces
- **Native MCP Client**: Direct protocol communication
- **Enhanced Interactive Client**: Rich CLI with comprehensive features
- **LangChain Integration**: AI-powered fraud analysis with GROQ API
- **Batch Processing**: Automated fraud detection workflows

### Deployment Options
- **Native Python**: Direct execution with uv package manager
- **Docker Container**: Production-ready containerization
- **Docker Compose**: Multi-service orchestration
- **Monitoring**: Optional Prometheus integration

## 📁 Project Structure

```
banking_fraud_mcp/
├── 🐳 Docker Files
│   ├── Dockerfile              # Container definition
│   ├── docker-compose.yml      # Multi-container setup
│   ├── docker-manage.sh        # Docker management script
│   ├── .dockerignore           # Build optimization
│   └── .env.example            # Environment template
│
├── 🖥️  Server & Core
│   ├── fraud_server.py         # Main MCP server
│   ├── fraud_tool.py           # Fraud detection logic
│   ├── db_setup.py             # Database initialization
│   └── fraud.json              # MCP client configuration
│
├── 👥 Client Applications
│   ├── mcp_fraud_client.py     # Native MCP client
│   ├── enhanced_client.py      # Enhanced interactive client
│   ├── client.py               # LangChain-powered client
│   ├── batch_fraud_client.py   # Batch processing client
│   └── simple_fraud_client.py  # Minimal example client
│
├── 🛠️  Management & Tools
│   ├── manage_server.sh        # Server management script
│   ├── pyproject.toml          # Python project configuration
│   └── uv.lock                 # Dependency lock file
│
├── 📊 Data & Config
│   ├── bank.db                 # DuckDB database file
│   ├── .env                    # Environment variables
│   └── inspector_config.json   # MCP Inspector config
│
└── 📚 Documentation
    ├── DOCKER.md               # Docker deployment guide
    └── README.md               # This file
```

## 🚀 Quick Start

### Option 1: Native Python (Recommended for Development)
```bash
# Start the server
./manage_server.sh start

# Run comprehensive demo
./manage_server.sh demo

# Interactive fraud analysis
./manage_server.sh interactive
```

### Option 2: Docker Deployment (Recommended for Production)
```bash
# Build and start container
./docker-manage.sh build
./docker-manage.sh start

# Run tests
./docker-manage.sh test
./docker-manage.sh db-status
```

## 🛠️ Management Commands

### Native Server Management
```bash
./manage_server.sh start          # Start MCP server
./manage_server.sh stop           # Stop server
./manage_server.sh status         # Check status
./manage_server.sh demo           # Run demo
./manage_server.sh interactive    # Interactive client
./manage_server.sh enhanced       # Enhanced client
./manage_server.sh langchain demo # AI-powered analysis
./manage_server.sh inspector      # Web inspector interface
./manage_server.sh setup-db       # Initialize database
./manage_server.sh db-status      # Database status
```

### Docker Container Management
```bash
./docker-manage.sh build         # Build image
./docker-manage.sh start         # Start container
./docker-manage.sh stop          # Stop container
./docker-manage.sh status        # Container status
./docker-manage.sh logs          # View logs
./docker-manage.sh shell         # Access shell
./docker-manage.sh test          # Run tests
./docker-manage.sh backup        # Backup data
./docker-manage.sh cleanup       # Clean up resources
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# GROQ API for LangChain integration
GROQ_API_KEY=your_groq_api_key_here

# Database configuration
DATABASE_PATH=./bank.db

# Fraud detection thresholds
HIGH_RISK_THRESHOLD=0.7
MEDIUM_RISK_THRESHOLD=0.4
LOW_RISK_THRESHOLD=0.2

# Application settings
LOG_LEVEL=INFO
DEBUG=false
```

### MCP Client Configuration (fraud.json)
```json
{
  "servers": {
    "fraud": {
      "command": "uv",
      "args": ["run", "python3", "fraud_server.py"],
      "cwd": "/path/to/banking_fraud_mcp"
    }
  }
}
```

## 🧪 Testing & Validation

### Comprehensive Demo
```bash
# Native Python
./manage_server.sh demo

# Docker
./docker-manage.sh test
```

### Interactive Testing
```bash
# Enhanced interactive client
./manage_server.sh enhanced

# AI-powered analysis
./manage_server.sh langchain demo
```

### Database Validation
```bash
# Check database status
./manage_server.sh db-status

# Docker version
./docker-manage.sh db-status
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Client Layer                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │   Native    │ │  Enhanced   │ │  LangChain  │   │
│  │ MCP Client  │ │   Client    │ │   Client    │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│                MCP Protocol Layer                   │
│                  (JSON-RPC over stdio)             │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│               MCP Server (FastMCP)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │    Tools    │ │  Resources  │ │   Prompts   │   │
│  │   - fraud   │ │ - status    │ │ - analysis  │   │
│  │ - statistics│ │ - patterns  │ │ - advisory  │   │
│  │   - risk    │ │ - samples   │ │             │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│               Business Logic Layer                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ Fraud Logic │ │ Risk Models │ │ Algorithms  │   │
│  │             │ │             │ │             │   │
│  └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────┐
│                 Data Layer                          │
│  ┌─────────────────────────────────────────────┐   │
│  │              DuckDB Database                │   │
│  │  ┌─────────────┐    ┌─────────────────┐    │   │
│  │  │  Customer   │    │  Transactions   │    │   │
│  │  │  Profiles   │    │                 │    │   │
│  │  └─────────────┘    └─────────────────┘    │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 🚦 Fraud Detection Capabilities

### Transaction Analysis
- **Real-time scoring**: Immediate fraud probability calculation
- **Historical patterns**: Analysis of customer transaction history
- **Geographic anomalies**: Location-based risk assessment
- **Amount thresholds**: Statistical deviation detection

### Customer Risk Profiling
- **Behavioral analysis**: Spending pattern recognition
- **Risk scoring**: Multi-factor risk calculation
- **Profile evolution**: Dynamic risk adjustment
- **Alert generation**: Automated suspicious activity detection

### Statistical Reporting
- **Fraud metrics**: System-wide fraud statistics
- **Trend analysis**: Temporal fraud pattern identification
- **Performance metrics**: Detection accuracy and efficiency
- **Compliance reporting**: Regulatory requirement fulfillment

## 🔒 Security Features

### Data Protection
- **Database encryption**: Data at rest protection
- **Secure communication**: MCP protocol security
- **Access control**: Authentication and authorization
- **Audit logging**: Comprehensive activity tracking

### Fraud Prevention
- **Multi-layered detection**: Comprehensive fraud analysis
- **Real-time alerts**: Immediate threat notification
- **Risk thresholds**: Configurable detection sensitivity
- **False positive reduction**: Advanced algorithm tuning

## 📊 Performance Characteristics

### Scalability
- **Async architecture**: High-concurrency support
- **Lightweight database**: Minimal resource footprint
- **Stateless design**: Horizontal scaling capability
- **Caching optimization**: Response time improvement

### Resource Usage
- **Memory**: ~256MB typical, 512MB maximum
- **CPU**: 0.25-0.5 cores under normal load
- **Storage**: ~50MB base, grows with transaction data
- **Network**: Minimal (stdio-based communication)

## 🔄 Integration Options

### MCP Ecosystem
- **Claude Desktop**: Direct integration support
- **MCP Inspector**: Web-based debugging interface
- **Third-party clients**: Standard MCP protocol compliance
- **Custom integrations**: Extensible architecture

### External Systems
- **Banking APIs**: Transaction data ingestion
- **Alert systems**: Notification integration
- **Compliance tools**: Regulatory reporting
- **Monitoring platforms**: Metrics and logging

## 🐛 Troubleshooting

### Common Issues
1. **Server won't start**: Check port availability and dependencies
2. **Database errors**: Verify database file permissions and integrity
3. **Client connection**: Ensure server is running and config is correct
4. **Docker issues**: Verify Docker daemon and image build

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
./manage_server.sh start --debug

# Docker debug mode
docker run -e DEBUG=true -e LOG_LEVEL=DEBUG banking-fraud-mcp
```

## 🎓 Development Guide

### Adding New Features
1. **New Tools**: Extend `fraud_server.py` with additional MCP tools
2. **Risk Models**: Enhance `fraud_tool.py` with new algorithms
3. **Data Sources**: Modify database schema in `db_setup.py`
4. **Client Features**: Extend client applications as needed

### Testing Strategy
- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end workflow validation
- **Performance tests**: Load and stress testing
- **Security tests**: Vulnerability assessment

## 📈 Future Enhancements

### Planned Features
- **Machine learning models**: Advanced pattern recognition
- **Real-time streaming**: Live transaction processing
- **Multi-bank support**: Cross-institution fraud detection
- **Advanced visualization**: Web dashboard interface

### Scalability Improvements
- **Distributed processing**: Multi-node deployment
- **Database sharding**: Large-scale data handling
- **API gateway**: HTTP REST interface
- **Microservices**: Component decoupling

## 🆘 Support & Maintenance

### Regular Maintenance
- **Database optimization**: Index maintenance and cleanup
- **Log rotation**: Prevent disk space issues
- **Dependency updates**: Security and feature updates
- **Performance monitoring**: Resource usage tracking

### Backup Strategy
- **Database backups**: Regular automated backups
- **Configuration backup**: Environment and settings
- **Container images**: Tagged version management
- **Disaster recovery**: Restoration procedures

## 📝 License & Attribution

This project demonstrates a comprehensive MCP server implementation for banking fraud detection. It showcases best practices for:
- MCP protocol implementation
- Database integration
- Multi-client support
- Docker containerization
- Production deployment

Built with FastMCP, DuckDB, and modern Python practices for reliability, performance, and maintainability.
