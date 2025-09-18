# Multi-stage build for Claude Multi-Agent System

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tmux \
    redis-tools \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Python dependencies
FROM base as dependencies

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Application
FROM dependencies as app

WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data logs web/static web/templates

# Set Python path
ENV PYTHONPATH=/app

# Stage 4: Development image
FROM app as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    flake8 \
    mypy \
    ipython

# Expose ports
EXPOSE 8000 8001 6379

# Default command for development
CMD ["python", "-m", "core.main"]

# Stage 5: Production image
FROM app as production

# Create non-root user
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /app

USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Expose ports
EXPOSE 8000 8001

# Production command with gunicorn
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--log-level", "info", \
     "--access-logfile", "-", "--error-logfile", "-", \
     "api.unified_gateway:app"]