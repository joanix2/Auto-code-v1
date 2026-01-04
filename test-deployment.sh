#!/bin/bash

# Test deployment locally before pushing to AWS
# This script helps verify that the docker-compose setup works correctly

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AutoCode Local Deployment Test              ║${NC}"
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env file created. Please edit it with your credentials.${NC}"
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to abort...${NC}"
    read
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Stop any existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker compose down 2>/dev/null || true

# Remove old volumes (optional, ask user)
read -p "$(echo -e ${YELLOW}Do you want to remove old volumes? This will delete all data. \(y/N\): ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🗑️  Removing volumes...${NC}"
    docker compose down -v
fi

# Build images
echo -e "${BLUE}🔨 Building Docker images...${NC}"
docker compose build --no-cache

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
docker compose up -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to start (30 seconds)...${NC}"
sleep 30

# Check service status
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
docker compose ps

# Health checks
echo ""
echo -e "${BLUE}🏥 Running health checks...${NC}"

check_service() {
    local name=$1
    local url=$2
    local max_attempts=5
    local attempt=1

    echo -n "  Checking $name... "
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s -o /dev/null "$url" 2>/dev/null; then
            echo -e "${GREEN}✅ OK${NC}"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ FAILED${NC}"
    return 1
}

# Check each service
check_service "Backend API" "http://localhost:8000/docs"
check_service "Frontend" "http://localhost:3000"
check_service "Neo4j" "http://localhost:7474"
check_service "NPM" "http://localhost:81"

# Display logs
echo ""
echo -e "${BLUE}📝 Recent logs:${NC}"
docker compose logs --tail=20

# Summary
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Deployment Test Complete                     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ All services are running!${NC}"
echo ""
echo -e "${YELLOW}Access your services at:${NC}"
echo -e "  ${BLUE}Frontend:${NC}   http://localhost:3000"
echo -e "  ${BLUE}Backend:${NC}    http://localhost:8000/docs"
echo -e "  ${BLUE}Neo4j:${NC}      http://localhost:7474"
echo -e "  ${BLUE}NPM Admin:${NC}  http://localhost:81"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo -e "  ${BLUE}View logs:${NC}       docker compose logs -f"
echo -e "  ${BLUE}Stop services:${NC}   docker compose stop"
echo -e "  ${BLUE}Restart:${NC}         docker compose restart"
echo -e "  ${BLUE}Full cleanup:${NC}    docker compose down -v"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
