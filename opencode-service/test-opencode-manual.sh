#!/bin/bash
# Quick test script for OpenCode in container
# This script creates a test project and runs OpenCode on it

echo "🧪 OpenCode Manual Test"
echo "======================="
echo ""

# Enter container and run test
docker exec -it autocode-opencode /bin/bash -c '
# Colors
GREEN="\033[0;32m"
BLUE="\033[0;34m"
YELLOW="\033[1;33m"
NC="\033[0m"

echo -e "${BLUE}Step 1: Creating test project${NC}"
cd /home/ubuntu/workspace
rm -rf opencode-test-python
mkdir opencode-test-python
cd opencode-test-python

# Initialize git
git init
git config user.name "OpenCode Test"
git config user.email "test@opencode.local"

echo -e "${GREEN}✅ Project created at: $(pwd)${NC}"
echo ""

echo -e "${BLUE}Step 2: Creating initial README${NC}"
cat > README.md << EOF
# OpenCode Test Project

Test project for OpenCode AI integration with Auto-Code.
EOF

git add README.md
git commit -m "Initial commit"
echo -e "${GREEN}✅ Initial commit created${NC}"
echo ""

echo -e "${BLUE}Step 3: Running OpenCode - Simple Task${NC}"
echo -e "${YELLOW}Task: Create a hello.py file with a hello world function${NC}"
echo ""

# Run OpenCode with a simple task
echo "Create a hello.py file with a simple hello_world() function that prints Hello, World! and returns the string. Add a main block that calls the function." | /home/ubuntu/.opencode/bin/opencode . --non-interactive

echo ""
echo -e "${BLUE}Step 4: Checking results${NC}"

if [ -f "hello.py" ]; then
    echo -e "${GREEN}✅ hello.py was created!${NC}"
    echo ""
    echo "Content:"
    echo "--------"
    cat hello.py
    echo ""
    echo "--------"
    
    # Test the file
    echo ""
    echo -e "${BLUE}Step 5: Testing the generated code${NC}"
    python3 hello.py
    
    echo ""
    echo -e "${GREEN}✅ Code executed successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  hello.py was not created${NC}"
    echo "Listing files:"
    ls -la
fi

echo ""
echo -e "${BLUE}Step 6: Checking git status${NC}"
git status --short

echo ""
echo -e "${GREEN}🎉 Test complete!${NC}"
echo ""
echo "You can now:"
echo "  - Enter container: docker exec -it autocode-opencode /bin/bash"
echo "  - Go to project: cd /home/ubuntu/workspace/opencode-test-python"
echo "  - Run OpenCode: echo \"your task\" | /home/ubuntu/.opencode/bin/opencode ."
'
