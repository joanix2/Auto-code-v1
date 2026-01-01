#!/bin/bash

# Auto-Code Platform Setup Script

echo "🚀 Auto-Code Platform Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your credentials:"
    echo "   - GITHUB_TOKEN"
    echo "   - GITHUB_OWNER"
    echo "   - GITHUB_REPO"
    echo "   - ANTHROPIC_API_KEY"
    echo ""
    echo "After editing .env, run this script again."
    exit 0
fi

echo "✅ .env file found"
echo ""

# Validate environment variables
source .env

if [ -z "$GITHUB_TOKEN" ] || [ "$GITHUB_TOKEN" = "your_github_token_here" ]; then
    echo "⚠️  GITHUB_TOKEN not set in .env file"
    echo "Please configure your GitHub token"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set in .env file"
    echo "Please configure your Anthropic API key"
    exit 1
fi

echo "✅ Environment variables configured"
echo ""

# Build and start containers
echo "🐳 Building and starting containers..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ All services are running!"
    echo ""
    echo "📱 Access points:"
    echo "   Frontend:  http://localhost:3000"
    echo "   Backend:   http://localhost:8000/api"
    echo "   API Docs:  http://localhost:8000/api/docs"
    echo "   RabbitMQ:  http://localhost:15672 (guest/guest)"
    echo ""
    echo "🎉 Setup complete! You can now create tasks from the PWA."
else
    echo "❌ Some services failed to start. Check logs with:"
    echo "   docker-compose logs"
fi
