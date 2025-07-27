# Banking Fraud Detection MCP Server with XGBoost ML - Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies including build tools for ML packages
RUN apt-get update && apt-get install -y \
    curl \
    lsof \
    build-essential \
    cmake \
    gcc \
    g++ \
    libomp-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies using uv (including ML packages)
RUN uv sync

# Copy the rest of the project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/logs

# Initialize database
RUN uv run python db_setup.py

# Pre-train ML models during build (optional - can be done at runtime)
RUN uv run python -c "from ml_fraud_detector import get_ml_detector; print('Training ML models...'); detector = get_ml_detector(); print('ML models ready')" || echo "ML models will be trained at runtime"

# Expose the port (though MCP uses stdio, this is for future HTTP endpoints)
EXPOSE 6277

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_SERVER_NAME=banking-fraud-detection
ENV DATABASE_PATH=/app/data/bank.db

# Health check script (create before switching to non-root user)
COPY <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import sys
import os
sys.path.append('/app')

try:
    import duckdb
    from fraud_server import get_database_path
    
    # Check if database is accessible
    db_path = get_database_path()
    conn = duckdb.connect(db_path)
    
    # Simple query to verify database health
    result = conn.execute("SELECT COUNT(*) FROM customer_profiles").fetchone()
    if not result or result[0] == 0:
        print("❌ Database appears empty")
        sys.exit(1)
    
    print(f"✅ Database healthy ({result[0]} customers)")
    
    # Check ML model availability
    try:
        from ml_fraud_detector import get_ml_detector
        detector = get_ml_detector()
        print("✅ ML models loaded and ready")
    except Exception as ml_e:
        print(f"⚠️ ML models not available: {ml_e}")
        print("✅ Will use rule-based detection fallback")
    
    print("✅ Banking fraud detection system is healthy")
    sys.exit(0)
        
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)
EOF

RUN chmod +x /app/healthcheck.py

# Create a non-root user for security and transfer ownership
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python /app/healthcheck.py

# Default command - start the MCP server
CMD ["uv", "run", "python", "fraud_server.py"]

# Labels for better container management
LABEL org.opencontainers.image.title="Banking Fraud Detection MCP Server"
LABEL org.opencontainers.image.description="A comprehensive MCP server for banking fraud detection with DuckDB backend"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="Banking Fraud Detection Team"
LABEL org.opencontainers.image.source="https://github.com/rahultube3/gen-ai-projects"
