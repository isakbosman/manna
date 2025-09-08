#!/bin/bash

# Database Reset Script for Manna Development Environment
# This script drops and recreates the PostgreSQL database

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🗑️ Resetting Manna Database..."

# Check if Docker Compose services are running
if ! docker-compose ps postgres | grep -q "Up"; then
    print_error "PostgreSQL service is not running. Please start it first with: docker-compose up -d postgres"
    exit 1
fi

# Warn user about data loss
print_warning "This will permanently delete ALL data in the database!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Stop services that depend on the database
print_status "Stopping dependent services..."
docker-compose stop backend frontend

# Drop all connections and reset database
print_status "Resetting database..."
docker-compose exec -T postgres psql -U manna_user -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'manna_db'
  AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS manna_db;
CREATE DATABASE manna_db;
GRANT ALL PRIVILEGES ON DATABASE manna_db TO manna_user;
"

if [ $? -eq 0 ]; then
    print_status "Database reset successfully"
else
    print_error "Failed to reset database"
    exit 1
fi

# Recreate tables using init script
print_status "Recreating database schema..."
docker-compose exec -T postgres psql -U manna_user -d manna_db -f /docker-entrypoint-initdb.d/init.sql

if [ $? -eq 0 ]; then
    print_status "Database schema recreated successfully"
else
    print_error "Failed to recreate database schema"
    exit 1
fi

# Restart services
print_status "Restarting services..."
docker-compose up -d backend frontend

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

print_status "Database reset complete! 🎉"
echo ""
echo "The database has been reset with:"
echo "  • Clean schema from init.sql"
echo "  • Default categories"
echo "  • All user data removed"
echo ""
echo "Services should now be ready at:"
echo "  • Frontend: http://localhost:8501"
echo "  • Backend:  http://localhost:8000"
echo "  • pgAdmin:  http://localhost:5050"
