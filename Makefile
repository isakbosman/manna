# Makefile for Manna Financial Management Platform
# Provides convenient shortcuts for common Docker operations

.PHONY: help setup start stop restart logs build clean reset seed validate status

# Default target
help:
	@echo "Manna Financial Management Platform - Docker Commands"
	@echo ""
	@echo "Setup Commands:"
	@echo "  make setup     - Initial setup (run once)"
	@echo "  make validate  - Validate setup and service health"
	@echo ""
	@echo "Development Commands:"
	@echo "  make start     - Start all services"
	@echo "  make stop      - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make status    - Show service status"
	@echo ""
	@echo "Database Commands:"
	@echo "  make reset     - Reset database (WARNING: destroys data)"
	@echo "  make seed      - Seed database with sample data"
	@echo ""
	@echo "Maintenance Commands:"
	@echo "  make logs      - Show all service logs"
	@echo "  make build     - Rebuild all images"
	@echo "  make clean     - Clean up Docker resources"
	@echo ""
	@echo "Individual Service Commands:"
	@echo "  make logs-backend   - Show backend logs"
	@echo "  make logs-frontend  - Show frontend logs"
	@echo "  make logs-db        - Show database logs"
	@echo "  make restart-backend   - Restart backend only"
	@echo "  make restart-frontend  - Restart frontend only"

# Setup and validation
setup:
	@echo "🚀 Setting up Manna development environment..."
	./scripts/dev-setup.sh

validate:
	@echo "🔍 Validating setup..."
	./scripts/validate-setup.sh

# Service management
start:
	@echo "🟢 Starting all services..."
	docker-compose up -d
	@echo "Services started! Use 'make validate' to check health."

stop:
	@echo "🛑 Stopping all services..."
	docker-compose down

restart:
	@echo "🔄 Restarting all services..."
	docker-compose restart

status:
	@echo "📊 Service Status:"
	docker-compose ps

# Database operations
reset:
	@echo "🗑️  Resetting database..."
	./scripts/db-reset.sh

seed:
	@echo "🌱 Seeding database..."
	./scripts/db-seed.sh

# Logs
logs:
	@echo "📋 Showing all logs (Ctrl+C to exit)..."
	docker-compose logs -f

logs-backend:
	@echo "📋 Showing backend logs (Ctrl+C to exit)..."
	docker-compose logs -f backend

logs-frontend:
	@echo "📋 Showing frontend logs (Ctrl+C to exit)..."
	docker-compose logs -f frontend

logs-db:
	@echo "📋 Showing database logs (Ctrl+C to exit)..."
	docker-compose logs -f postgres

logs-redis:
	@echo "📋 Showing Redis logs (Ctrl+C to exit)..."
	docker-compose logs -f redis

# Individual service restarts
restart-backend:
	@echo "🔄 Restarting backend..."
	docker-compose restart backend

restart-frontend:
	@echo "🔄 Restarting frontend..."
	docker-compose restart frontend

restart-db:
	@echo "🔄 Restarting database..."
	docker-compose restart postgres

# Build and maintenance
build:
	@echo "🔨 Building all images..."
	docker-compose build

build-backend:
	@echo "🔨 Building backend image..."
	docker-compose build backend

build-frontend:
	@echo "🔨 Building frontend image..."
	docker-compose build frontend

rebuild:
	@echo "🔨 Rebuilding and restarting all services..."
	docker-compose up -d --build

# Cleanup
clean:
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down
	docker system prune -f
	docker volume prune -f

clean-all:
	@echo "⚠️  WARNING: This will remove ALL Docker data including volumes!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v
	docker system prune -af
	docker volume prune -f

# Development helpers
shell-backend:
	@echo "🐚 Opening shell in backend container..."
	docker-compose exec backend /bin/bash

shell-frontend:
	@echo "🐚 Opening shell in frontend container..."
	docker-compose exec frontend /bin/bash

shell-db:
	@echo "🐚 Opening PostgreSQL shell..."
	docker-compose exec postgres psql -U manna_user -d manna_db

# Quick access URLs
open:
	@echo "🌐 Opening application URLs..."
	@echo "Frontend: http://localhost:8501"
	@echo "Backend API: http://localhost:8000/docs"
	@echo "pgAdmin: http://localhost:5050"
	@if command -v open >/dev/null 2>&1; then \
		open http://localhost:8501; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open http://localhost:8501; \
	fi

# Production deployment
prod-start:
	@echo "🚀 Starting production services..."
	docker-compose -f docker-compose.prod.yml up -d

prod-stop:
	@echo "🛑 Stopping production services..."
	docker-compose -f docker-compose.prod.yml down

prod-logs:
	@echo "📋 Showing production logs..."
	docker-compose -f docker-compose.prod.yml logs -f

# Health checks
health:
	@echo "🏥 Checking service health..."
	@echo "Backend API:"
	@curl -f -s http://localhost:8000/health || echo "Backend not responding"
	@echo ""
	@echo "Frontend:"
	@curl -f -s http://localhost:8501/_stcore/health || echo "Frontend not responding"
	@echo ""
	@echo "Database:"
	@docker-compose exec -T postgres pg_isready -U manna_user -d manna_db || echo "Database not ready"
	@echo "Redis:"
	@docker-compose exec -T redis redis-cli -a manna_redis_password ping 2>/dev/null || echo "Redis not responding"

# Environment setup
env-setup:
	@echo "⚙️  Setting up environment file..."
	@if [ ! -f .env ]; then \
		cp docker.env.sample .env; \
		echo "Created .env file from template"; \
		echo "Please update Plaid credentials and other settings"; \
	else \
		echo ".env file already exists"; \
	fi
