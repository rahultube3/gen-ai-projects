# Banking Fraud Detection MCP Server - Dockerfile
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    lsof \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy project files
COPY . .

# Install Python dependencies using uv
RUN uv sync

# Create database directory and initialize
RUN mkdir -p /app/data
RUN uv run python db_setup.py

# Expose the port (though MCP uses stdio, this is for future HTTP endpoints)
EXPOSE 6277

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_SERVER_NAME=banking-fraud-detection
ENV DATABASE_PATH=/app/data/bank.db

# Create a non-root user for security
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Health check script
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
    if result and result[0] > 0:
        print("✅ Banking fraud detection system is healthy")
        sys.exit(0)
    else:
        print("❌ Database appears empty")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Health check failed: {e}")
    sys.exit(1)
EOF

RUN chmod +x /app/healthcheck.py

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
