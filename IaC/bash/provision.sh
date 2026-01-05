#!/bin/bash

# Provision and deploy AutoCode infrastructure on AWS
# This script runs terraform and then deploys the application

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== AutoCode Infrastructure Provisioning ===${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: terraform is not installed${NC}"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo -e "${RED}Error: aws cli is not installed${NC}"
    exit 1
fi

# Check SSH keys
SSH_KEY_PATH="${SSH_KEY_PATH:-~/.ssh/aws_key.pem}"
SSH_PUB_KEY_PATH="${SSH_PUB_KEY_PATH:-~/.ssh/aws_key.pem.pub}"

if [ ! -f "$SSH_KEY_PATH" ] || [ ! -f "$SSH_PUB_KEY_PATH" ]; then
    echo -e "${YELLOW}SSH keys not found. Generating new keys...${NC}"
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/aws_key.pem -N ""
    echo -e "${GREEN}SSH keys generated${NC}"
fi

# Navigate to IaC directory
cd "$(dirname "$0")/.."

# Initialize Terraform
echo -e "${YELLOW}Initializing Terraform...${NC}"
terraform init

# Plan
echo -e "${YELLOW}Planning infrastructure changes...${NC}"
terraform plan -out=tfplan

# Ask for confirmation
read -p "Do you want to apply these changes? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 0
fi

# Apply
echo -e "${YELLOW}Applying infrastructure changes...${NC}"
terraform apply tfplan

# Wait for instance to be ready
echo -e "${YELLOW}Waiting for instance to be fully ready (60 seconds)...${NC}"
sleep 60

# Deploy application
echo -e "${YELLOW}Deploying application...${NC}"
bash ./bash/deploy-app.sh

echo -e "${GREEN}=== Provisioning and deployment complete ===${NC}"

# Display outputs
echo ""
echo "=== Infrastructure Details ==="
terraform output

echo ""
echo -e "${GREEN}All done! 🚀${NC}"
