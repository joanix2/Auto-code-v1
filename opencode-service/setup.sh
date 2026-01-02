#!/bin/bash
# Setup script for OpenCode service
# Run this once to configure the environment

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

echo "🔧 OpenCode Service Setup"
echo "========================="
echo ""

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo "⚠️  .env file already exists."
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled."
        exit 1
    fi
fi

# Get GitHub token from backend or ask user
BACKEND_ENV="$SCRIPT_DIR/../backend/.env"
if [ -f "$BACKEND_ENV" ]; then
    echo "🔍 Looking for GitHub token in backend .env..."
    GITHUB_TOKEN=$(grep "^GITHUB_TOKEN=" "$BACKEND_ENV" | cut -d '=' -f2)
    
    if [ -n "$GITHUB_TOKEN" ]; then
        echo "✅ Found GitHub token in backend .env"
        USE_BACKEND_TOKEN="y"
    else
        echo "⚠️  No GitHub token found in backend .env"
        USE_BACKEND_TOKEN="n"
    fi
else
    USE_BACKEND_TOKEN="n"
fi

# Ask for token if not found
if [ "$USE_BACKEND_TOKEN" != "y" ]; then
    echo ""
    echo "📝 Please enter your GitHub Personal Access Token"
    echo "   Generate one at: https://github.com/settings/tokens"
    echo "   Required scopes: repo, workflow"
    echo ""
    read -p "GitHub Token: " GITHUB_TOKEN
    
    if [ -z "$GITHUB_TOKEN" ]; then
        echo "❌ Token cannot be empty"
        exit 1
    fi
fi

# Create .env file
cat > "$ENV_FILE" << EOF
# OpenCode Service - Environment Configuration
# Auto-generated on $(date)

# GitHub Personal Access Token (required)
GH_TOKEN=$GITHUB_TOKEN

# Optional: Custom paths (uncomment to override defaults)
# OPENCODE_SSH_KEY=~/.ssh/id_ed25519
# OPENCODE_AUTH_FILE=~/.local/share/opencode/auth.json
# OPENCODE_CONFIG_DIR=~/.config/opencode

# Docker container name
# CONTAINER_NAME=autocode-opencode

# Docker image name
# IMAGE_NAME=autocode-opencode-service
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""

# Check for SSH key
echo "🔑 Checking SSH configuration..."
if [ -f "$HOME/.ssh/id_ed25519" ]; then
    echo "   ✅ SSH key found: ~/.ssh/id_ed25519"
elif [ -f "$HOME/.ssh/id_rsa" ]; then
    echo "   ✅ SSH key found: ~/.ssh/id_rsa"
else
    echo "   ⚠️  No SSH key found"
    echo "   Generate one with: ssh-keygen -t ed25519 -C 'your_email@example.com'"
fi

# Check for OpenCode auth
echo ""
echo "🔐 Checking OpenCode authentication..."
if [ -f "$HOME/.local/share/opencode/auth.json" ]; then
    echo "   ✅ OpenCode auth file found"
else
    echo "   ⚠️  OpenCode not authenticated"
    echo "   Run: opencode auth login"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Build the Docker image:  ./manage-opencode.sh build"
echo "  2. Start the container:     ./manage-opencode.sh start"
echo "  3. Check status:            ./manage-opencode.sh status"
echo ""
