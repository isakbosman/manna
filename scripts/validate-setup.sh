#!/bin/bash

# Validation script for Manna Docker setup
# This script validates that all services are running correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[x]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

echo "🔍 Validating Manna Docker Setup..."
echo ""

# Check if Docker is running
print_info "Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running or accessible"
    exit 1
fi
print_status "Docker is running"

# Check if services are up
print_info "Checking service status..."
services=("postgres" "redis" "backend" "frontend" "pgadmin")
all_up=true

for service in "${services[@]}"; do
    if docker-compose ps $service | grep -q "Up"; then
        print_status "$service is running"
    else
        print_error "$service is not running"
        all_up=false
    fi
done

if [ "$all_up" = false ]; then
    print_error "Some services are not running. Use 'docker-compose up -d' to start them."
    exit 1
fi

# Test service connectivity
print_info "Testing service connectivity..."

# Test PostgreSQL
if docker-compose exec -T postgres pg_isready -U manna_user -d manna_db >/dev/null 2>&1; then
    print_status "PostgreSQL is accepting connections"
else
    print_error "PostgreSQL is not accepting connections"
fi

# Test Redis
if docker-compose exec -T redis redis-cli -a manna_redis_password ping 2>/dev/null | grep -q "PONG"; then
    print_status "Redis is responding"
else
    print_error "Redis is not responding"
fi

# Test Backend API
if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
    print_status "Backend API is responding"
else
    print_warning "Backend API may not be ready yet (this is normal on first start)"
fi

# Test Frontend
if curl -f -s http://localhost:8501/_stcore/health >/dev/null 2>&1; then
    print_status "Frontend is responding"
else
    print_warning "Frontend may not be ready yet (this is normal on first start)"
fi

# Test pgAdmin
if curl -f -s http://localhost:5050/misc/ping >/dev/null 2>&1; then
    print_status "pgAdmin is responding"
else
    print_warning "pgAdmin may not be ready yet"
fi

# Check environment variables
print_info "Checking environment configuration..."
if [ -f ".env" ]; then
    print_status ".env file exists"
    
    # Check for placeholder values
    if grep -q "your_plaid_client_id" .env; then
        print_warning "Plaid Client ID still contains placeholder value"
    fi
    
    if grep -q "your_plaid_secret" .env; then
        print_warning "Plaid Secret still contains placeholder value"
    fi
    
    if grep -q "your_encryption_key_here" .env; then
        print_warning "Encryption key still contains placeholder value"
    fi
else
    print_error ".env file not found"
fi

# Check volumes
print_info "Checking data persistence..."
if docker volume ls | grep -q "manna.*postgres"; then
    print_status "PostgreSQL data volume exists"
fi

if docker volume ls | grep -q "manna.*redis"; then
    print_status "Redis data volume exists"
fi

# Final status
echo ""
print_info "Validation complete!"
echo ""
echo "🌐 Access Points:"
echo "  Frontend:    http://localhost:8501"
echo "  Backend API: http://localhost:8000/docs"
echo "  pgAdmin:     http://localhost:5050"
echo ""
echo "🔧 Management Commands:"
echo "  View logs:       docker-compose logs -f [service]"
echo "  Restart service: docker-compose restart [service]"
echo "  Stop all:        docker-compose down"
echo "  Reset database:  ./scripts/db-reset.sh"
echo "  Seed data:       ./scripts/db-seed.sh"
echo ""

if [ -f ".env" ] && grep -q "your_plaid" .env; then
    print_warning "Remember to update your Plaid credentials in .env file!"
fi

print_status "Setup validation complete! 🎉"
