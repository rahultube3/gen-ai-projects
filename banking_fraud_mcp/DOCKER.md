# Banking Fraud Detection MCP Server - Docker Deployment

This directory contains Docker configuration for containerizing the Banking Fraud Detection MCP Server.

## 🐳 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 512MB RAM available

### 1. Build and Start
```bash
# Build the Docker image
./docker-manage.sh build

# Start the container
./docker-manage.sh start
```

### 2. Test the Deployment
```bash
# Check container status
./docker-manage.sh status

# Run fraud detection tests
./docker-manage.sh test

# Check database status
./docker-manage.sh db-status
```

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `Dockerfile` | Main container definition |
| `docker-compose.yml` | Multi-container orchestration |
| `docker-manage.sh` | Container management script |
| `.dockerignore` | Files to exclude from build |
| `.env.example` | Environment configuration template |

## 🛠️ Management Commands

### Container Lifecycle
```bash
./docker-manage.sh build     # Build the image
./docker-manage.sh start     # Start container
./docker-manage.sh stop      # Stop container
./docker-manage.sh restart   # Restart container
./docker-manage.sh status    # Show status
./docker-manage.sh logs      # View logs
./docker-manage.sh shell     # Access container shell
```

### Application Testing
```bash
./docker-manage.sh test      # Run MCP client tests
./docker-manage.sh db-status # Check database status
```

### Data Management
```bash
./docker-manage.sh backup    # Backup application data
./docker-manage.sh restore backup.tar.gz  # Restore from backup
./docker-manage.sh cleanup   # Clean up Docker resources
```

## ⚙️ Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
# Required for LangChain integration
GROQ_API_KEY=your_groq_api_key_here

# Database configuration
DATABASE_PATH=/app/data/bank.db

# Fraud detection thresholds
HIGH_RISK_THRESHOLD=0.7
MEDIUM_RISK_THRESHOLD=0.4
LOW_RISK_THRESHOLD=0.2
```

### Volume Mounts
- `./data` → `/app/data` (Database files)
- `./logs` → `/app/logs` (Application logs)

### Port Mapping
- `6277:6277` (MCP server port)

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│           Docker Container          │
│  ┌─────────────────────────────────┐│
│  │     Banking Fraud MCP Server    ││
│  │                                 ││
│  │  ┌─────────────┐ ┌─────────────┐││
│  │  │   FastMCP   │ │   DuckDB    │││
│  │  │   Server    │ │  Database   │││
│  │  └─────────────┘ └─────────────┘││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
           │
    ┌─────────────┐
    │ Host System │
    │   - Data    │
    │   - Logs    │
    └─────────────┘
```

## 🔍 Monitoring

### Health Checks
The container includes automatic health checks:
- Interval: 30 seconds
- Timeout: 10 seconds  
- Retries: 3
- Start period: 10 seconds

### Logging
- JSON format logs
- 10MB max file size
- 3 file rotation
- Available via `docker logs`

## 🚀 Production Deployment

### Resource Limits
```yaml
resources:
  limits:
    memory: 512M
    cpus: '0.5'
  reservations:
    memory: 256M
    cpus: '0.25'
```

### Security Features
- Non-root user (mcpuser)
- Minimal base image (python:3.13-slim)
- Health checks
- Resource constraints

### Scaling with Docker Compose
```bash
# Scale to multiple instances
docker-compose up --scale banking-fraud-mcp=3

# Load balancer configuration required for multiple instances
```

## 🐛 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   ./docker-manage.sh logs
   
   # Verify environment
   cat .env
   ```

2. **Database errors**
   ```bash
   # Check database status
   ./docker-manage.sh db-status
   
   # Recreate database
   ./docker-manage.sh shell
   uv run python db_setup.py
   ```

3. **Permission issues**
   ```bash
   # Fix data directory permissions
   sudo chown -R 1000:1000 ./data ./logs
   ```

### Debug Mode
```bash
# Run container with debug logging
docker run -it --rm \
  -e LOG_LEVEL=DEBUG \
  -e DEBUG=true \
  -v $(pwd)/data:/app/data \
  banking-fraud-mcp
```

## 📊 Performance Tuning

### Memory Optimization
- Adjust `memory` limits in docker-compose.yml
- Monitor usage: `docker stats banking-fraud-detection`

### CPU Optimization
- Adjust `cpus` limits for your workload
- Use multiple instances for high throughput

### Database Optimization
- Mount database on SSD storage
- Adjust DuckDB configuration in fraud_server.py

## 🔐 Security Considerations

- Change default SECRET_KEY in production
- Use secrets management for GROQ_API_KEY
- Regular security updates of base image
- Network isolation with custom networks
- Monitor container logs for anomalies

## 📈 Monitoring Integration

Optional Prometheus monitoring:
```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access Prometheus at http://localhost:9090
```

## 🆘 Support

For issues with Docker deployment:
1. Check container logs: `./docker-manage.sh logs`
2. Verify health status: `./docker-manage.sh status`
3. Test database connectivity: `./docker-manage.sh db-status`
4. Run diagnostic tests: `./docker-manage.sh test`
