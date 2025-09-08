#!/bin/bash

# Manna Development Environment Setup Script
# This script initializes the Docker development environment

set -e  # Exit on any error

echo "🚀 Setting up Manna Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

# Check prerequisites
print_header "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Docker and Docker Compose are installed."

# Check if running on Apple Silicon
if [[ $(uname -m) == "arm64" ]]; then
    print_warning "Detected Apple Silicon (M1/M2). Using platform-specific configurations."
    export DOCKER_DEFAULT_PLATFORM=linux/amd64
fi

# Create environment file if it doesn't exist
print_header "Setting up environment variables..."

if [ ! -f ".env" ]; then
    if [ -f "docker.env.sample" ]; then
        cp docker.env.sample .env
        print_status "Created .env file from docker.env.sample"
        print_warning "Please update the .env file with your actual values:"
        echo "  - PLAID_CLIENT_ID"
        echo "  - PLAID_SECRET"
        echo "  - ENCRYPTION_KEY"
        echo "  - SECRET_KEY"
    else
        print_error "docker.env.sample file not found. Cannot create .env file."
        exit 1
    fi
else
    print_status ".env file already exists."
fi

# Generate encryption key if needed
print_header "Generating security keys..."

if grep -q "your_encryption_key_here" .env 2>/dev/null; then
    if command -v python3 &> /dev/null; then
        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
        sed -i.bak "s/your_encryption_key_here/$ENCRYPTION_KEY/g" .env
        print_status "Generated new encryption key"
    else
        print_warning "Python3 not found. Please manually generate an encryption key."
    fi
fi

if grep -q "your_secret_key_here" .env 2>/dev/null; then
    if command -v python3 &> /dev/null; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        sed -i.bak "s/your_secret_key_here/$SECRET_KEY/g" .env
        print_status "Generated new secret key"
    else
        print_warning "Python3 not found. Please manually generate a secret key."
    fi
fi

# Create necessary directories
print_header "Creating directories..."
mkdir -p data logs docker/nginx/ssl
touch logs/.gitkeep data/.gitkeep
print_status "Created data and logs directories"

# Build Docker images
print_header "Building Docker images..."
docker-compose build --parallel
if [ $? -eq 0 ]; then
    print_status "Docker images built successfully"
else
    print_error "Failed to build Docker images"
    exit 1
fi

# Start services
print_header "Starting services..."
docker-compose up -d
if [ $? -eq 0 ]; then
    print_status "Services started successfully"
else
    print_error "Failed to start services"
    exit 1
fi

# Wait for services to be ready
print_header "Waiting for services to be ready..."

echo "Waiting for PostgreSQL..."
while ! docker-compose exec -T postgres pg_isready -U manna_user -d manna_db > /dev/null 2>&1; do
    sleep 1
done
print_status "PostgreSQL is ready"

echo "Waiting for Redis..."
while ! docker-compose exec -T redis redis-cli -a manna_redis_password ping > /dev/null 2>&1; do
    sleep 1
done
print_status "Redis is ready"

# Run database migrations if needed
print_header "Setting up database..."
# Add migration commands here when available
print_status "Database setup complete"

# Display service information
print_header "Development environment is ready!"
echo ""
echo "📊 Services running:"
echo "  • Frontend (Streamlit):  http://localhost:8501"
echo "  • Backend API (FastAPI): http://localhost:8000"
echo "  • PostgreSQL:            localhost:5432"
echo "  • Redis:                 localhost:6379"
echo "  • pgAdmin:               http://localhost:5050"
echo ""
echo "🔧 Useful commands:"
echo "  • View logs:        docker-compose logs -f [service]"
echo "  • Stop services:    docker-compose down"
echo "  • Restart services: docker-compose restart"
echo "  • Reset database:   ./scripts/db-reset.sh"
echo ""
echo "📝 Next steps:"
echo "  1. Update your Plaid credentials in .env file"
echo "  2. Visit http://localhost:8501 to access the dashboard"
echo "  3. Check logs with: docker-compose logs -f"
echo ""
print_status "Setup complete! Happy coding! 🎉"
