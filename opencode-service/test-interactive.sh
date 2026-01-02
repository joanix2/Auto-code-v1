#!/bin/bash
# Interactive OpenCode Test
# This provides commands to test OpenCode manually

cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║         🧪 OpenCode Interactive Test Guide                     ║
╔════════════════════════════════════════════════════════════════╝

📋 Quick Commands:

1️⃣  Enter the container:
   docker exec -it autocode-opencode /bin/bash

2️⃣  Once inside, navigate to test project:
   cd /home/ubuntu/workspace/opencode-test-python

3️⃣  Run OpenCode with a task:
   /home/ubuntu/.opencode/bin/opencode run "Create a hello.py file with a hello_world() function"

4️⃣  Or start OpenCode TUI (interactive mode):
   /home/ubuntu/.opencode/bin/opencode .

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Example Tasks to Try:

• Simple Python:
  /home/ubuntu/.opencode/bin/opencode run "Create a Python calculator with add, subtract, multiply, divide functions"

• Web scraper:
  /home/ubuntu/.opencode/bin/opencode run "Create a web scraper that fetches GitHub trending repositories"

• API client:
  /home/ubuntu/.opencode/bin/opencode run "Create a REST API client for JSONPlaceholder with GET and POST methods"

• Data processing:
  /home/ubuntu/.opencode/bin/opencode run "Create a CSV parser that reads sales data and calculates totals"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 OpenCode Commands Reference:

• opencode run "task"         - Run a task non-interactively
• opencode .                  - Start interactive TUI
• opencode auth status        - Check authentication
• opencode models             - List available models
• opencode stats              - Show usage statistics
• opencode session            - Manage sessions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚀 Let's start! Running automated setup...

EOF

echo "Setting up test project..."
docker exec autocode-opencode /bin/bash -c '
cd /home/ubuntu/workspace
rm -rf opencode-test-python
mkdir opencode-test-python
cd opencode-test-python
git init
git config user.name "OpenCode Test"
git config user.email "test@opencode.local"
cat > README.md << EOFREADME
# OpenCode Test Project

This is a test project for OpenCode AI.
EOFREADME
git add README.md
git commit -m "Initial commit"
echo "✅ Test project ready at: /home/ubuntu/workspace/opencode-test-python"
'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Ready! Now run:"
echo ""
echo "   docker exec -it autocode-opencode /bin/bash"
echo ""
echo "Then inside the container:"
echo ""
echo "   cd /home/ubuntu/workspace/opencode-test-python"
echo "   /home/ubuntu/.opencode/bin/opencode run \"Create a hello.py with a function that prints Hello World\""
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
