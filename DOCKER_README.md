# Manna Financial Management Platform - Docker Development Environment

This guide provides comprehensive instructions for setting up and running the Manna Financial Management Platform using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Service Details](#service-details)
- [Environment Configuration](#environment-configuration)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

Before setting up the development environment, ensure you have:

### Required Software

- **Docker Desktop** (4.0+)
  - [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - For Apple Silicon (M1/M2): Ensure "Use Rosetta for x86/amd64 emulation" is enabled
  - For Windows: Ensure WSL2 backend is enabled

- **Docker Compose** (2.0+)
  - Included with Docker Desktop
  - Verify installation: `docker-compose --version`

### System Requirements

- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: At least 10GB free space
- **Network**: Internet connection for pulling images and Plaid API

### Plaid API Credentials

1. Sign up at [Plaid Dashboard](https://dashboard.plaid.com/)
2. Create a new application
3. Note your `client_id` and `secret` (sandbox/development)

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to project directory
cd /path/to/manna

# Run the automated setup script
./scripts/dev-setup.sh
```

The setup script will:

- Check prerequisites
- Create environment configuration
- Generate security keys
- Build Docker images
- Start all services
- Initialize the database

### 2. Configure Environment Variables

Edit the generated `.env` file:

```bash
# Edit with your preferred editor
nano .env

# Update these required values:
PLAID_CLIENT_ID=your_actual_client_id
PLAID_SECRET=your_actual_secret
```

### 3. Access Services

Once setup is complete, access:

- **Frontend Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Database Admin**: http://localhost:5050
  - Email: `admin@manna.local`
  - Password: `admin`

### 4. Seed Development Data (Optional)

```bash
# Add sample data for testing
./scripts/db-seed.sh
```

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend     │    │   PostgreSQL    │
│  (Streamlit)    │◄──►│   (FastAPI)     │◄──►│   Database      │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └─────────────►│     Redis       │◄─────────────┘
                        │    Cache        │
                        │   Port: 6379    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │    pgAdmin      │
                        │ (DB Management) │
                        │   Port: 5050    │
                        └─────────────────┘
```

## Service Details

### Frontend (Streamlit)

- **Port**: 8501
- **Purpose**: Interactive dashboard for financial data visualization
- **Features**: Transaction views, reports, account management
- **Hot Reload**: Enabled in development mode

### Backend (FastAPI)

- **Port**: 8000
- **Purpose**: RESTful API for data processing and business logic
- **Features**: Plaid integration, transaction processing, report generation
- **Documentation**: Available at `/docs` and `/redoc`

### PostgreSQL Database

- **Port**: 5432
- **Purpose**: Primary data storage
- **Features**: Transaction data, account information, categorization rules
- **Persistence**: Data persisted in Docker volumes

### Redis Cache

- **Port**: 6379
- **Purpose**: Session storage and caching
- **Features**: Fast data retrieval, session management

### pgAdmin

- **Port**: 5050
- **Purpose**: Database administration interface
- **Access**: Web-based PostgreSQL management

## Environment Configuration

### Development Environment (`.env`)

Key configuration variables:

```bash
# Database
DATABASE_URL=postgresql://manna_user:manna_password@postgres:5432/manna_db

# Plaid API
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ENV=development  # or sandbox, production

# Security
ENCRYPTION_KEY=generated_key
SECRET_KEY=generated_secret

# Application
ENVIRONMENT=development
DEBUG=true
```

### Production Environment

For production deployment, use `docker-compose.prod.yml`:

```bash
# Copy production environment template
cp docker.env.sample .env.prod

# Edit with production values
nano .env.prod

# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d
```

## Development Workflow

### Daily Development

```bash
# Start services
docker-compose up -d

# View logs (all services)
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Code Changes

- **Frontend changes**: Auto-reload enabled, changes reflect immediately
- **Backend changes**: Auto-reload enabled for API changes
- **Database schema**: Use migration scripts or reset database

### Database Management

```bash
# Reset database (WARNING: destroys all data)
./scripts/db-reset.sh

# Seed with sample data
./scripts/db-seed.sh

# Access database directly
docker-compose exec postgres psql -U manna_user -d manna_db
```

### Service Management

```bash
# Restart specific service
docker-compose restart backend

# Rebuild service after Dockerfile changes
docker-compose up -d --build backend

# View service status
docker-compose ps

# Execute commands in containers
docker-compose exec backend /bin/bash
docker-compose exec frontend /bin/bash
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check if ports are in use
sudo lsof -i :8501  # Frontend
sudo lsof -i :8000  # Backend
sudo lsof -i :5432  # PostgreSQL

# Check Docker resources
docker system df
docker system prune  # Clean up if needed
```

#### Database Connection Issues

```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready -U manna_user -d manna_db

# Check logs
docker-compose logs postgres

# Reset database
./scripts/db-reset.sh
```

#### Plaid API Issues

```bash
# Verify environment variables
docker-compose exec backend printenv | grep PLAID

# Check API connectivity
docker-compose exec backend curl -f http://localhost:8000/health
```

#### Performance Issues

```bash
# Check resource usage
docker stats

# Increase Docker Desktop resources:
# Docker Desktop → Preferences → Resources
# Recommended: 4 CPUs, 8GB RAM
```

### Apple Silicon (M1/M2) Specific

```bash
# If you encounter architecture issues:
export DOCKER_DEFAULT_PLATFORM=linux/amd64

# Rebuild images
docker-compose build --no-cache
```

### Windows WSL2 Specific

```bash
# Ensure WSL2 is properly configured
wsl --set-default-version 2

# Check Docker integration
docker context use desktop-linux
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f --tail=100

# Service-specific debugging
docker-compose exec backend python -c "import sys; print(sys.path)"
```

## Production Deployment

### Using Production Configuration

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# With custom environment
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Key Production Differences

- **Security**: Non-root users, minimal images
- **Performance**: Optimized build stages, resource limits
- **Monitoring**: Health checks, restart policies
- **SSL**: Nginx reverse proxy with SSL termination

### SSL Configuration (Production)

```bash
# Place SSL certificates in:
mkdir -p docker/nginx/ssl/
# Add cert.pem and key.pem files

# Update nginx.conf to enable HTTPS block
```

## Port Reference

| Service    | Port | Purpose                    |
| ---------- | ---- | -------------------------- |
| Frontend   | 8501 | Streamlit Dashboard        |
| Backend    | 8000 | FastAPI Application        |
| PostgreSQL | 5432 | Database Server            |
| Redis      | 6379 | Cache Server               |
| pgAdmin    | 5050 | Database Administration    |
| Nginx      | 80   | Reverse Proxy (Production) |
| Nginx SSL  | 443  | HTTPS (Production)         |

## Useful Commands Reference

```bash
# Quick setup
./scripts/dev-setup.sh

# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service_name]

# Rebuild after changes
docker-compose up -d --build [service_name]

# Database operations
./scripts/db-reset.sh    # Reset database
./scripts/db-seed.sh     # Add sample data

# Access containers
docker-compose exec [service] /bin/bash

# Check service health
docker-compose ps
curl http://localhost:8000/health
```

---

**Need Help?** Check the troubleshooting section or create an issue in the repository.
