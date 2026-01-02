# Claude Opus 4 Agent with LangGraph

Advanced AI agent for autonomous ticket development using Claude Opus 4 and LangGraph workflow orchestration.

## Overview

This module provides a sophisticated AI agent that can autonomously develop features and fix bugs based on ticket descriptions. It uses:

- **Claude Opus 4.5**: Latest and most powerful Claude model for code generation
- **LangGraph**: State machine framework for complex multi-step workflows
- **FastAPI Integration**: RESTful API endpoints for triggering agent workflows

## Architecture

```
backend/src/agent/
├── __init__.py           # Module exports
├── claude_agent.py       # Main ClaudeAgent class with workflow methods
├── workflow.py           # LangGraph workflow definitions
├── config.py            # Configuration constants
└── README.md            # This file
```

### Components

#### 1. **ClaudeAgent** (`claude_agent.py`)
Main agent class with:
- `analyze_ticket()`: Analyzes requirements and creates development plan
- `generate_code()`: Generates implementation code
- `review_and_test()`: Reviews code and suggests tests
- `should_continue()`: Decision function for workflow control
- `run()`: Main entry point that executes complete workflow

#### 2. **AgentState** (`claude_agent.py`)
Pydantic model tracking agent state:
- Ticket information (id, title, description, type, priority)
- Repository details (path, URL)
- Workflow state (messages, iterations, errors, status)
- Generated artifacts (code changes)

#### 3. **Workflow Types** (`workflow.py`)

**Standard Workflow** (`DevelopmentWorkflow`):
```
analyze_ticket → generate_code → review_and_test → END
```

**Iterative Workflow** (`IterativeWorkflow`):
```
analyze_ticket → generate_code → review_and_test
                        ↑              ↓
                        └── refine_code ←┘
```

**Test-Driven Development** (`TestDrivenWorkflow`):
```
analyze_ticket → generate_tests → generate_code → review_and_test → END
```

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Required packages:
- `anthropic>=0.40.0` - Anthropic API client
- `langgraph>=0.2.54` - LangGraph framework
- `langchain-core>=0.3.26` - LangChain core utilities
- `langchain-anthropic>=0.3.5` - Anthropic integration for LangChain

### 2. Configure Environment

Add to `backend/.env`:

```env
# Claude Opus 4 Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...your-key-here...

# Optional: Override model version
# CLAUDE_MODEL=claude-opus-4-20250514
```

Get your API key from: https://console.anthropic.com/

## Usage

### API Endpoint

**POST** `/api/agent/develop-ticket`

Trigger autonomous development for a ticket:

```bash
curl -X POST "http://localhost:8000/api/agent/develop-ticket" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "ticket-uuid-here",
    "workflow_type": "standard",
    "max_iterations": 20
  }'
```

**Request Parameters:**
- `ticket_id` (required): UUID of the ticket to develop
- `workflow_type` (optional): `"standard"`, `"iterative"`, or `"tdd"` (default: `"standard"`)
- `max_iterations` (optional): Maximum workflow iterations (default: `20`)

**Response:**
```json
{
  "success": true,
  "ticket_id": "ticket-uuid",
  "status": "completed",
  "iterations": 3,
  "message": "Agent workflow completed",
  "details": {
    "code_changes": [...],
    "errors": [],
    "messages": [...]
  }
}
```

### Programmatic Usage

```python
from src.agent.claude_agent import ClaudeAgent

# Initialize agent
agent = ClaudeAgent(api_key="sk-ant-...")

# Run workflow
result = await agent.run(
    ticket_id="abc-123",
    ticket_title="Add user authentication",
    ticket_description="Implement JWT-based authentication...",
    ticket_type="feature",
    priority="high",
    repository_path="/path/to/repo",
    repository_url="https://github.com/user/repo",
    max_iterations=20
)

# Check result
if result["success"]:
    print(f"✅ Completed in {result['iterations']} iterations")
    for change in result["code_changes"]:
        print(f"Modified: {change}")
else:
    print(f"❌ Failed: {result['errors']}")
```

### Choosing Workflow Type

**Use Standard** when:
- Single-pass development is sufficient
- Ticket requirements are clear and simple
- Quick iteration needed

**Use Iterative** when:
- Complex requirements need refinement
- Code quality is critical
- Multiple revision cycles expected

**Use TDD** when:
- Test coverage is paramount
- API contracts need definition first
- Following strict TDD methodology

## Workflow Details

### 1. Analysis Phase
- Parses ticket description and requirements
- Breaks down task into concrete steps
- Identifies files to create/modify
- Plans implementation approach
- Considers edge cases

**Output**: Detailed development plan with file-level granularity

### 2. Code Generation Phase
- Generates complete, production-ready code
- Follows best practices and patterns
- Includes error handling
- Adds explanatory comments
- Ensures maintainability

**Output**: JSON with file paths, content, and explanations

### 3. Review Phase
- Reviews generated code for quality
- Identifies potential bugs
- Checks security implications
- Evaluates performance
- Suggests test cases

**Output**: Comprehensive code review with recommendations

## Configuration

Edit `backend/src/agent/config.py`:

```python
# Model Configuration
CLAUDE_MODEL = "claude-opus-4-20250514"  # Model version
MAX_ITERATIONS = 20  # Max workflow steps

# Temperature Settings
DEFAULT_TEMPERATURE = 0.3  # Lower = more deterministic

# Token Limits
ANALYSIS_MAX_TOKENS = 4096
CODE_GENERATION_MAX_TOKENS = 8000
REVIEW_MAX_TOKENS = 4096

# Default Workflow
DEFAULT_WORKFLOW = "standard"  # or "iterative" or "tdd"
```

## State Management

The agent maintains state through `AgentState`:

```python
class AgentState(BaseModel):
    # Ticket Info
    ticket_id: str
    ticket_title: str
    ticket_description: str
    
    # Repository
    repository_path: str
    repository_url: str
    
    # Workflow State
    messages: List[Dict]      # Conversation history
    iterations: int           # Current iteration
    current_task: str         # Current workflow step
    code_changes: List[Dict]  # Generated code
    errors: List[str]         # Error log
    status: str              # initialized, analyzing, coding, testing, completed, failed
```

## Error Handling

The agent handles errors gracefully:

1. **API Errors**: Caught and logged, status set to "failed"
2. **Iteration Limit**: Auto-stops at `max_iterations` to prevent infinite loops
3. **State Corruption**: State always preserved in errors list
4. **Workflow Failures**: Returns partial results with error details

## Logging

The agent logs all activities:

```python
import logging
logger = logging.getLogger(__name__)

# Log levels used:
logger.info()    # Workflow progress
logger.warning() # Recoverable issues
logger.error()   # Failures and exceptions
```

View logs in console or configure file logging in `main.py`.

## Integration with Frontend

The agent integrates with the existing development button:

```typescript
// In TicketsList.tsx or similar
const handleDevelop = async (tickets: Ticket[]) => {
  const response = await fetch('/api/agent/develop-ticket', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ticket_id: tickets[0].id,
      workflow_type: 'standard'
    })
  });
  
  const result = await response.json();
  if (result.success) {
    // Update UI, show success
  }
};
```

## Limitations

- **Cost**: Claude Opus 4 is expensive (~$15/$75 per million tokens)
- **Speed**: Opus prioritizes quality over speed (30-60s per response)
- **Context**: Limited to ticket description (doesn't read full codebase yet)
- **Execution**: Generates code but doesn't execute/test it automatically
- **Git**: Doesn't commit changes (manual or use OpenCode for that)

## Roadmap

Future enhancements:

- [ ] **Codebase Analysis**: Read existing code for context
- [ ] **Execution & Testing**: Run generated code and tests
- [ ] **Git Integration**: Auto-commit and create PRs
- [ ] **Multi-file Projects**: Handle complex multi-file changes
- [ ] **Interactive Mode**: Allow human feedback in workflow
- [ ] **Cost Optimization**: Smart caching and prompt optimization
- [ ] **Streaming**: Stream responses for real-time updates

## Troubleshooting

### "Import could not be resolved" errors
- Run `pip install -r requirements.txt` in backend directory
- Ensure virtual environment is activated

### "ANTHROPIC_API_KEY not found"
- Add `ANTHROPIC_API_KEY=sk-ant-...` to `backend/.env`
- Restart backend server

### Agent returns failed status
- Check logs for specific error
- Verify ticket has valid repository
- Ensure repository path exists
- Check API key is valid and has credits

### Workflow takes too long
- Reduce `max_iterations` in request
- Use "standard" instead of "iterative" workflow
- Consider using Claude Haiku for faster (but lower quality) results

## Contributing

To extend the agent:

1. **Add new workflow nodes** in `claude_agent.py`
2. **Create custom workflows** in `workflow.py`
3. **Update configuration** in `config.py`
4. **Add tests** for new functionality

## License

Part of Auto-Code Platform. See main LICENSE file.
