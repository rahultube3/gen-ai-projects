# HR Assistant Docker Deployment Guide

This guide explains how to deploy the HR Assistant system using Docker containers.

## Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Compose** (included with Docker Desktop)
3. **OpenAI API Key** for LLM functionality

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.docker .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

**Required Changes in .env:**
- `OPENAI_API_KEY=your_actual_openai_api_key`
- `MONGO_PASSWORD=your_secure_password`

### 2. Start Services

```bash
# Using management script (recommended)
./manage_docker.sh start

# Or using docker compose directly
docker compose up -d
```

### 3. Access the Application

- **Streamlit Chat Interface**: http://localhost:8501
- **RAG API Documentation**: http://localhost:8001/docs
- **Comprehensive API Documentation**: http://localhost:8002/docs
- **MongoDB**: mongodb://localhost:27017

## Management Commands

The `manage_docker.sh` script provides convenient commands:

```bash
# Start all services
./manage_docker.sh start

# Check service health
./manage_docker.sh status

# View logs
./manage_docker.sh logs
./manage_docker.sh logs streamlit-chat  # specific service

# Restart services
./manage_docker.sh restart

# Stop services
./manage_docker.sh stop

# Build images
./manage_docker.sh build

# Backup data
./manage_docker.sh backup

# Clean up resources
./manage_docker.sh cleanup

# Open shell in container
./manage_docker.sh shell mongodb
```

## Architecture

The deployment consists of 4 main services:

### 1. MongoDB (`mongodb`)
- **Purpose**: Document storage and vector database
- **Port**: 27017 (internal), 27017 (external)
- **Data**: Persistent volume storage
- **Health Check**: Connection test every 30s

### 2. RAG API (`rag-api`)
- **Purpose**: RAG system with vector search
- **Port**: 8001
- **Dependencies**: MongoDB
- **Health Check**: HTTP endpoint `/health`

### 3. Comprehensive API (`comprehensive-api`)
- **Purpose**: Full HR assistant API with guardrails
- **Port**: 8002
- **Dependencies**: MongoDB
- **Health Check**: HTTP endpoint `/health`

### 4. Streamlit Chat (`streamlit-chat`)
- **Purpose**: Web-based chat interface
- **Port**: 8501
- **Dependencies**: RAG API, Comprehensive API
- **Health Check**: HTTP endpoint

## Service Communication

Services communicate through a custom Docker network:
- **Network Name**: `hr-assistant-network`
- **Internal DNS**: Services can reach each other by service name
- **Security**: Only exposed ports are accessible externally

## Data Persistence

### MongoDB Data
- **Volume**: `mongodb_data`
- **Location**: `/data/db` in container
- **Backup**: Use `./manage_docker.sh backup`

### Logs
- **Volume**: `logs_data`
- **Location**: `/app/logs` in containers
- **Access**: View with `./manage_docker.sh logs`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `MONGO_PASSWORD` | MongoDB admin password | `secure_password_change_this` |
| `RAG_TOP_K` | Number of RAG results | `5` |
| `LLM_MODEL` | OpenAI model to use | `gpt-3.5-turbo` |
| `CACHE_ENABLED` | Enable response caching | `true` |
| `ENABLE_GUARDRAILS` | Enable content filtering | `true` |

### Port Configuration

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| MongoDB | 27017 | 27017 | Database access |
| RAG API | 8001 | 8001 | RAG endpoints |
| Comprehensive API | 8002 | 8002 | Full API |
| Streamlit | 8501 | 8501 | Web interface |

## Security Features

### Container Security
- **Non-root users** in all containers
- **Read-only root filesystems** where possible
- **Minimal base images** (Python slim)
- **Security scanning** with Docker Scout

### Network Security
- **Internal network** for service communication
- **No direct database access** from external
- **Health checks** for service monitoring

### Data Security
- **Guardrails system** prevents sensitive data leaks
- **Content filtering** for PII and confidential information
- **Access logging** and violation tracking

## Monitoring

### Health Checks
All services include health checks:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts

### Logs
View logs for debugging:
```bash
# All services
./manage_docker.sh logs

# Specific service
./manage_docker.sh logs rag-api

# Follow logs in real-time
docker compose logs -f streamlit-chat
```

### Performance Monitoring
The Streamlit interface includes:
- **Cache hit rates**
- **Response times**
- **Memory usage**
- **Active connections**

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker status
docker info

# Check service logs
./manage_docker.sh logs

# Rebuild images
./manage_docker.sh build
```

#### Database Connection Issues
```bash
# Check MongoDB logs
./manage_docker.sh logs mongodb

# Verify network connectivity
docker compose exec rag-api ping mongodb
```

#### API Endpoints Not Responding
```bash
# Check service health
./manage_docker.sh status

# Test endpoints directly
curl http://localhost:8001/health
curl http://localhost:8002/health
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor cache performance in Streamlit UI
# Look for low cache hit rates
```

### Log Locations

| Service | Log Location | Description |
|---------|-------------|-------------|
| All Services | `/app/logs/` | Application logs |
| MongoDB | Docker logs | Database operations |
| Docker | System logs | Container operations |

## Backup and Recovery

### Creating Backups
```bash
# Automated backup
./manage_docker.sh backup

# Manual MongoDB backup
docker compose exec mongodb mongodump --uri="mongodb://admin:password@localhost:27017/hr_assistant?authSource=admin"
```

### Restoring from Backup
```bash
# Stop services
./manage_docker.sh stop

# Restore data volume
docker volume rm hr-assistant_mongodb_data
docker volume create hr-assistant_mongodb_data

# Copy backup data
# (restore commands depend on backup format)

# Restart services
./manage_docker.sh start
```

## Development

### Building Custom Images
```bash
# Build all images
docker compose build

# Build specific service
docker compose build rag-api

# No cache build
docker compose build --no-cache
```

### Development Mode
For development, you can mount local code:
```bash
# Add to docker-compose.yml service
volumes:
  - ./src:/app/src:ro  # Read-only code mount
```

### Testing
```bash
# Run tests in container
docker compose exec rag-api python -m pytest

# Interactive testing
./manage_docker.sh shell rag-api
```

## Production Deployment

### Scaling
```bash
# Scale specific services
docker compose up -d --scale rag-api=3

# Load balancer configuration needed for multiple instances
```

### Security Hardening
1. **Change default passwords** in `.env`
2. **Use secrets management** for API keys
3. **Enable TLS/SSL** for external access
4. **Configure firewall** rules
5. **Regular security updates**

### Monitoring Integration
- **Prometheus**: Add metrics endpoints
- **Grafana**: Create monitoring dashboards
- **ELK Stack**: Centralized logging
- **Health checks**: External monitoring

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review service logs
3. Verify configuration
4. Test component isolation

The system is designed to be resilient with automatic restarts and health monitoring.
