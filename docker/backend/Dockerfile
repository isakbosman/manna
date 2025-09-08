# Multi-stage Dockerfile for Manna Backend (FastAPI)

# Base Python image with conda support
FROM continuumio/miniconda3:latest as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Create conda environment and install dependencies
RUN conda create -n manna python=3.11 -y && \
    echo "source activate manna" > ~/.bashrc

# Activate environment and install packages
SHELL ["/bin/bash", "-c"]
RUN source activate manna && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install fastapi uvicorn[standard] httpx pytest-asyncio

# Development stage
FROM base as development

# Install development dependencies
RUN source activate manna && \
    pip install --no-cache-dir \
    watchfiles \
    pytest-xdist \
    pre-commit \
    ipython \
    jupyter

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Development command with hot reload
CMD ["/bin/bash", "-c", "source activate manna && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"]

# Production stage
FROM base as production

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r manna && useradd -r -g manna manna && \
    chown -R manna:manna /app

# Switch to non-root user
USER manna

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["/bin/bash", "-c", "source activate manna && uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4"]