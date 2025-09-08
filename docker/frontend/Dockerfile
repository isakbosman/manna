# Multi-stage Dockerfile for Manna Frontend (Streamlit)

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
    pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN source activate manna && \
    pip install --no-cache-dir \
    watchdog \
    streamlit-autorefresh \
    streamlit-authenticator

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/.streamlit

# Copy Streamlit config
COPY docker/frontend/streamlit_config.toml /app/.streamlit/config.toml

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Development command
CMD ["/bin/bash", "-c", "source activate manna && streamlit run src/dashboard/app.py --server.address 0.0.0.0 --server.port 8501 --server.runOnSave true"]

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
RUN mkdir -p /app/data /app/logs /app/.streamlit

# Copy Streamlit config
COPY docker/frontend/streamlit_config.toml /app/.streamlit/config.toml

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Production command
CMD ["/bin/bash", "-c", "source activate manna && streamlit run src/dashboard/app.py --server.address 0.0.0.0 --server.port 8501"]