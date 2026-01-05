#!/bin/bash

# Script to sync .env to Terraform variables and configure GitHub secrets
# Usage: ./sync-env-to-terraform.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
IAC_DIR="$PROJECT_ROOT/IaC"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AutoCode - Sync .env to Terraform Variables      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Error: .env file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Run: cp .env.example .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found .env file${NC}"

# Source the .env file
set -a
source "$ENV_FILE"
set +a

# Validate required variables
REQUIRED_VARS=(
    "GITHUB_TOKEN"
    "NEO4J_PASSWORD"
    "ANTHROPIC_API_KEY"
)

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ] || [ "${!var}" = "your_"* ] || [ "${!var}" = "sk-ant-"* ] || [ "${!var}" = "ghp_"* ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Missing or invalid values in .env:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "   - ${YELLOW}$var${NC}"
    done
    echo ""
    echo -e "${YELLOW}Please edit .env and fill in the required values.${NC}"
    echo -e "${YELLOW}See ENV_SETUP_GUIDE.md for help.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All required .env variables are set${NC}"
echo ""

# Export Terraform variables
echo -e "${BLUE}Configuring Terraform variables...${NC}"

# GitHub configuration
export TF_VAR_github_owner="joanix2"
export TF_VAR_github_repo="Auto-code-v1"
export TF_VAR_github_token="$GITHUB_TOKEN"

# AWS configuration
export TF_VAR_aws_region="eu-west-3"
export TF_VAR_project_name="autocode"

# Secret values to be configured in GitHub
export TF_VAR_neo4j_password="$NEO4J_PASSWORD"
export TF_VAR_gh_token="$GITHUB_TOKEN"
export TF_VAR_anthropic_api_key="$ANTHROPIC_API_KEY"

# SSH key path
export TF_VAR_ssh_private_key_path="$HOME/.ssh/aws_key.pem"
export TF_VAR_ssh_public_key_path="$HOME/.ssh/aws_key.pem.pub"

echo -e "${GREEN}✓ Terraform variables exported${NC}"
echo ""

# Show configuration
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  GitHub Owner:     $TF_VAR_github_owner"
echo "  GitHub Repo:      $TF_VAR_github_repo"
echo "  AWS Region:       $TF_VAR_aws_region"
echo "  Project Name:     $TF_VAR_project_name"
echo "  Neo4j Password:   ${NEO4J_PASSWORD:0:4}***"
echo "  GitHub Token:     ${GITHUB_TOKEN:0:8}***"
echo "  Anthropic Key:    ${ANTHROPIC_API_KEY:0:10}***"
echo "  SSH Key:          $TF_VAR_ssh_private_key_path"
echo ""

# Ask for confirmation
read -p "$(echo -e ${YELLOW}Do you want to apply Terraform changes now? \(y/N\): ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Terraform variables are exported in this shell.${NC}"
    echo -e "${YELLOW}You can run terraform commands manually:${NC}"
    echo ""
    echo "  cd IaC"
    echo "  terraform init"
    echo "  terraform plan"
    echo "  terraform apply"
    echo ""
    exit 0
fi

# Change to IaC directory
cd "$IAC_DIR"

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo -e "${BLUE}Initializing Terraform...${NC}"
    terraform init
fi

# Plan
echo -e "${BLUE}Planning Terraform changes...${NC}"
terraform plan -out=tfplan

# Ask for final confirmation
echo ""
read -p "$(echo -e ${YELLOW}Apply these changes? \(y/N\): ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Terraform plan saved to tfplan${NC}"
    echo -e "${YELLOW}Run 'terraform apply tfplan' to apply manually${NC}"
    exit 0
fi

# Apply
echo -e "${BLUE}Applying Terraform changes...${NC}"
terraform apply tfplan

# Clean up plan file
rm -f tfplan

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Configuration Complete!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}GitHub Secrets have been automatically configured!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Check GitHub Actions secrets in your repo settings"
echo "  2. Push code to trigger deployment: git push origin main"
echo "  3. Monitor deployment: https://github.com/joanix2/Auto-code-v1/actions"
echo ""
