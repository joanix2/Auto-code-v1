# Quick Start: Claude Opus 4 Agent

Get started with the LangGraph-based AI agent in 5 minutes.

## Prerequisites

- Python 3.11+
- Active Anthropic API account
- Backend server configured

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `anthropic` - Claude API client
- `langgraph` - Workflow framework
- `langchain-anthropic` - Anthropic integration
- `langchain-core` - Core utilities

## Step 2: Get API Key

1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Navigate to API Keys section
4. Create new API key
5. Copy the key (starts with `sk-ant-`)

## Step 3: Configure Environment

Add to `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...
```

## Step 4: Start Backend

```bash
cd backend
python main.py
```

Server starts at `http://localhost:8000`

## Step 5: Test the Agent

### Via Swagger UI

1. Open http://localhost:8000/docs
2. Authenticate with JWT token
3. Navigate to **agent** section
4. Try `POST /api/agent/develop-ticket`
5. Provide:
   ```json
   {
     "ticket_id": "your-ticket-uuid",
     "workflow_type": "standard",
     "max_iterations": 20
   }
   ```

### Via cURL

```bash
curl -X POST "http://localhost:8000/api/agent/develop-ticket" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "abc-123",
    "workflow_type": "standard"
  }'
```

### Via Python

```python
import asyncio
from src.agent.claude_agent import ClaudeAgent

async def test_agent():
    agent = ClaudeAgent()
    
    result = await agent.run(
        ticket_id="test-1",
        ticket_title="Add login page",
        ticket_description="Create a simple login page with email/password",
        ticket_type="feature",
        priority="high",
        repository_path="/path/to/your/repo",
        repository_url="https://github.com/user/repo",
        max_iterations=10
    )
    
    print(f"Success: {result['success']}")
    print(f"Status: {result['status']}")
    print(f"Iterations: {result['iterations']}")
    
    if result['code_changes']:
        print("\nCode Changes:")
        for change in result['code_changes']:
            print(f"  - {change}")

# Run it
asyncio.run(test_agent())
```

## Expected Output

Successful run:

```json
{
  "success": true,
  "ticket_id": "abc-123",
  "status": "completed",
  "iterations": 3,
  "message": "Agent workflow completed",
  "details": {
    "code_changes": [
      {
        "iteration": 2,
        "output": "...",
        "timestamp": "2024-01-15T10:30:00"
      }
    ],
    "errors": [],
    "messages": [
      {
        "role": "assistant",
        "content": "Analysis complete...",
        "step": "analysis"
      },
      {
        "role": "assistant",
        "content": "Code generated...",
        "step": "code_generation"
      },
      {
        "role": "assistant",
        "content": "Review complete...",
        "step": "review"
      }
    ]
  }
}
```

## Troubleshooting

### ImportError: No module named 'anthropic'
```bash
pip install anthropic langgraph langchain-anthropic langchain-core
```

### "ANTHROPIC_API_KEY not found"
Check your `.env` file has the key:
```bash
cat backend/.env | grep ANTHROPIC
```

### Rate limit errors
- Wait a few seconds between requests
- Anthropic has rate limits for API calls
- Consider implementing exponential backoff

### Agent returns failed status
Check logs:
```bash
# In backend console
# Look for ERROR lines with agent details
```

## Next Steps

- Read full documentation: `backend/src/agent/README.md`
- Try different workflow types: `iterative`, `tdd`
- Integrate with frontend development button
- Configure custom workflows
- Adjust token limits and temperature

## Cost Awareness

**Claude Opus 4 Pricing** (as of Jan 2025):
- Input: ~$15 per million tokens
- Output: ~$75 per million tokens

**Typical ticket costs**:
- Simple ticket: ~10,000 tokens = $0.15 - $0.75
- Complex ticket: ~50,000 tokens = $0.75 - $3.75

Monitor usage at https://console.anthropic.com/

## Support

For issues or questions:
1. Check `backend/src/agent/README.md`
2. Review logs in backend console
3. Test API key at https://console.anthropic.com/
4. Verify all dependencies installed

Happy coding with AI! 🤖✨
