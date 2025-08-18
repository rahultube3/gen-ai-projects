# HR Assistant Streamlit Chat Interface
# Multi-stage Docker build for production deployment

# Stage 1: Base Python environment
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies installation
FROM base as dependencies

# Create and set working directory
WORKDIR /app

# Copy requirements files
COPY requirements.txt requirements_basic.txt ./
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install streamlit plotly pandas

# Stage 3: Application
FROM base as application

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application files
COPY streamlit_chat.py ./
COPY simple_chat.py ./
COPY guardrails.py ./
COPY rag_system.py ./
COPY ingest_mongodb.py ./
COPY comprehensive_api.py ./
COPY .env ./

# Copy sample data directory if it exists
COPY sample_data/ ./sample_data/

# Create logs directory
RUN mkdir -p logs && chown -R app:app /app

# Switch to non-root user
USER app

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command to run Streamlit
CMD ["streamlit", "run", "streamlit_chat.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
