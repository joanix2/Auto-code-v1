#!/bin/bash

# Deploy AutoCode to AWS EC2
# This script deploys the application after Terraform has provisioned the infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== AutoCode Deployment Script ===${NC}"

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform is not installed${NC}"
    exit 1
fi

# Get instance IP from terraform output
echo -e "${YELLOW}Getting instance IP from Terraform...${NC}"
INSTANCE_IP=$(terraform output -raw public_ip 2>/dev/null)

if [ -z "$INSTANCE_IP" ]; then
    echo -e "${RED}Error: Could not get instance IP. Make sure terraform apply has been run.${NC}"
    exit 1
fi

echo -e "${GREEN}Instance IP: $INSTANCE_IP${NC}"

# SSH key path - expand ~ to home directory
SSH_KEY="${SSH_KEY:-$HOME/.ssh/aws_key.pem}"

if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}Error: SSH key not found at $SSH_KEY${NC}"
    exit 1
fi

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
ssh -i "$SSH_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP "echo 'SSH connection successful'" || {
    echo -e "${RED}Error: Could not connect to instance${NC}"
    exit 1
}

# Deploy the application
echo -e "${YELLOW}Deploying application...${NC}"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP << 'ENDSSH'
set -e

echo "=== Setting up application ==="

# Navigate to home directory
cd /home/ubuntu

# Check if app directory exists and is a git repository
if [ -d "app/.git" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd app
    git pull origin main || echo "Warning: Could not pull latest changes"
elif [ -d "app" ]; then
    echo "Directory exists but is not a git repository, removing and cloning fresh..."
    rm -rf app
    git clone https://github.com/joanix2/Auto-code-v1.git app
    cd app
else
    echo "Cloning repository..."
    git clone https://github.com/joanix2/Auto-code-v1.git app
    cd app
fi

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# GitHub Token (replace with your token)
GITHUB_TOKEN=your_github_token_here

# Anthropic API Key (replace with your key)
ANTHROPIC_API_KEY=your_anthropic_key_here

# Environment
ENVIRONMENT=production

# Backend Configuration
BACKEND_URL=http://backend:8000
FRONTEND_URL=http://localhost:3000
EOF
    echo "⚠️  Please edit /home/ubuntu/app/.env with your actual credentials"
fi

# Stop existing containers
echo "Stopping existing containers..."
docker compose down 2>/dev/null || true

# Build and start containers
echo "Building and starting containers..."
docker compose up -d --build

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 10

# Check container status
echo "Container status:"
docker compose ps

echo "=== Deployment complete ==="
echo ""
echo "Access your application at:"
echo "  Frontend:   http://$(curl -s ifconfig.me):3000"
echo "  Backend:    http://$(curl -s ifconfig.me):8000"
echo "  Neo4j:      http://$(curl -s ifconfig.me):7474"
echo "  NPM Admin:  http://$(curl -s ifconfig.me):81"
echo ""
echo "⚠️  Don't forget to configure your .env file!"
ENDSSH

echo -e "${GREEN}=== Deployment completed successfully ===${NC}"
echo ""
echo "Application URLs:"
echo "  Frontend:   http://$INSTANCE_IP:3000"
echo "  Backend:    http://$INSTANCE_IP:8000/docs"
echo "  Neo4j:      http://$INSTANCE_IP:7474"
echo "  NPM Admin:  http://$INSTANCE_IP:81"
echo ""
echo "To configure environment variables:"
echo "  ssh -i $SSH_KEY ubuntu@$INSTANCE_IP"
echo "  nano /home/ubuntu/app/.env"
echo ""
echo "To view logs:"
echo "  ssh -i $SSH_KEY ubuntu@$INSTANCE_IP 'cd /home/ubuntu/app && docker compose logs -f'"
