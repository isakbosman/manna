#!/bin/bash

# Manna Financial Platform - Development Setup Script

set -e

echo "🚀 Setting up Manna Financial Platform..."

# Check if running in manna conda environment
if [ "$CONDA_DEFAULT_ENV" != "manna" ]; then
    echo "⚠️  Please activate the manna conda environment first:"
    echo "   conda activate manna"
    exit 1
fi

# Check if pnpm is installed
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
pnpm install

# Build shared package
echo "🔧 Building shared package..."
cd packages/shared
pnpm build
cd ../..

# Install Python backend dependencies in conda environment
echo "🐍 Installing Python dependencies..."
cd packages/backend
pip install -r requirements.txt
cd ../..

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.sample .env
    echo "⚠️  Please update .env with your actual configuration values"
fi

# Start Docker services
echo "🐳 Starting Docker services (PostgreSQL and Redis)..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Update .env with your Plaid API credentials"
echo "   2. Run 'pnpm dev' to start the development server"
echo "   3. Visit http://localhost:3000 for the frontend"
echo "   4. Visit http://localhost:8000 for the backend API"
echo ""
echo "📚 Available commands:"
echo "   pnpm dev        - Start both frontend and backend in development mode"
echo "   pnpm build      - Build all packages"
echo "   pnpm lint       - Run linting"
echo "   pnpm format     - Format code"
echo "   pnpm type-check - Run TypeScript type checking"