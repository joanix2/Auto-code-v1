# LangGraph Implementation - State Machine Workflow

## 🎯 Réponse aux Questions

### Question 1: "Tu as bien utilisé LangGraph pour faire une machine à état ?"

**✅ OUI** - LangGraph est maintenant utilisé pour **tout le workflow** (pas seulement l'agent).

**Fichier principal** : `backend/src/services/ticket_workflow.py` (~600 lignes)

### Question 2: "Est-ce que tu as géré les différents repos à pull dans un workspace ?"

**✅ OUI** - Workspace structure améliorée avec `owner/repo`.

**Fichier** : `backend/src/services/git_service.py`

---

## Architecture LangGraph

### 1. State Definition (Pydantic)

```python
class TicketProcessingState(BaseModel):
    """State for the ticket processing workflow"""

    # Ticket information
    ticket_id: str
    ticket: Optional[Ticket] = None
    repository: Optional[Any] = None

    # Repository paths
    repo_path: Optional[str] = None
    branch_name: Optional[str] = None

    # Conversation with LLM
    conversation: List[Message] = []
    last_message: Optional[Message] = None

    # Processing results
    llm_response: Optional[Dict[str, Any]] = None
    ci_result: Optional[CIResult] = None

    # State tracking
    iteration_count: int = 0
    has_uncommitted_changes: bool = False
    error: Optional[str] = None
    status: str = "OPEN"
```

### 2. Workflow Graph

```
                         START
                           │
                           ▼
                 ┌─────────────────┐
                 │check_iterations │ (1)
                 │MAX_ITERATIONS=5 │
                 └────────┬────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
          EXCEEDED                CONTINUE
              │                       │
              ▼                       ▼
      ┌──────────────┐      ┌──────────────────┐
      │create_bug    │      │prepare_repository│ (2)
      │_ticket       │      │Clone/Pull/Branch │
      └──────┬───────┘      └────────┬─────────┘
             │                       │
             ▼                       ▼
           END           ┌─────────────────────┐
                         │load_conversation    │ (3)
                         │Get/Create Messages  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    call_llm         │ (4)
                         │ ClaudeAgent.run()   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                    NO CHANGES           HAS CHANGES
                         │                     │
                         ▼                     ▼
                       END           ┌─────────────────┐
                                     │commit_changes   │ (5)
                                     │Git commit       │
                                     └────────┬────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │    run_ci       │ (6)
                                     │pytest/npm/make  │
                                     └────────┬────────┘
                                              │
                                              ▼
                                     ┌─────────────────┐
                                     │handle_ci_result │ (7)
                                     │Check CI status  │
                                     └────────┬────────┘
                                              │
                               ┌──────────────┴──────────────┐
                               │                             │
                          CI FAILED                      CI PASSED
                               │                             │
                 ┌─────────────┴──────────┐                 │
                 │                        │                 │
         iterations < MAX        iterations >= MAX          │
                 │                        │                 │
                 ▼                        ▼                 ▼
         ┌──────────────┐      ┌──────────────┐   ┌────────────────┐
         │   call_llm   │      │create_bug    │   │await_validation│ (8)
         │ (with error) │      │_ticket       │   │PENDING_VAL     │
         └──────┬───────┘      └──────┬───────┘   └────────────────┘
                │                     │                    │
                └──────────┬──────────┘                    │
                           │                               │
                           ▼                               ▼
                         END                             END
```

### 3. Nodes (9 étapes)

```python
workflow.add_node("check_iterations", self._check_iterations)
workflow.add_node("prepare_repository", self._prepare_repository)
workflow.add_node("load_conversation", self._load_conversation)
workflow.add_node("call_llm", self._call_llm)
workflow.add_node("commit_changes", self._commit_changes)
workflow.add_node("run_ci", self._run_ci)
workflow.add_node("handle_ci_result", self._handle_ci_result)
workflow.add_node("await_validation", self._await_validation)
workflow.add_node("create_bug_ticket", self._create_bug_ticket)
```

#### Node Descriptions

| Node                   | Description                             | Input                   | Output                       |
| ---------------------- | --------------------------------------- | ----------------------- | ---------------------------- |
| **check_iterations**   | Vérifie si MAX_ITERATIONS (5) dépassé   | State initial           | State avec ticket chargé     |
| **prepare_repository** | Clone/pull repo, crée branche, rebase   | State avec ticket       | State avec repo_path, branch |
| **load_conversation**  | Charge messages ou crée message initial | State avec repo         | State avec conversation      |
| **call_llm**           | Appelle ClaudeAgent pour code           | State avec conversation | State avec llm_response      |
| **commit_changes**     | Git commit si changements               | State avec LLM response | State commité                |
| **run_ci**             | Exécute tests (pytest/npm/make)         | State commité           | State avec ci_result         |
| **handle_ci_result**   | Analyse résultat CI                     | State avec CI result    | State avec status updated    |
| **await_validation**   | État final PENDING_VALIDATION           | State CI OK             | État final                   |
| **create_bug_ticket**  | Crée bug ticket si échec                | State échec             | État final                   |

### 4. Conditional Edges (Décisions)

```python
# After check_iterations
workflow.add_conditional_edges(
    "check_iterations",
    self._should_continue_after_check,
    {
        "continue": "prepare_repository",
        "create_bug": "create_bug_ticket"
    }
)

# After call_llm
workflow.add_conditional_edges(
    "call_llm",
    self._should_commit,
    {
        "commit": "commit_changes",
        "end": END
    }
)

# After handle_ci_result
workflow.add_conditional_edges(
    "handle_ci_result",
    self._should_retry_or_validate,
    {
        "retry": "call_llm",
        "validate": "await_validation",
        "create_bug": "create_bug_ticket"
    }
)
```

#### Decision Functions

```python
def _should_continue_after_check(self, state: TicketProcessingState) -> str:
    """Decide whether to continue or create bug ticket"""
    if state.iteration_count >= MAX_ITERATIONS:
        return "create_bug"
    return "continue"

def _should_commit(self, state: TicketProcessingState) -> str:
    """Decide whether to commit changes"""
    if state.has_uncommitted_changes:
        return "commit"
    return "end"

def _should_retry_or_validate(self, state: TicketProcessingState) -> str:
    """Decide next step after CI"""
    if state.ci_result and state.ci_result.failed:
        if state.iteration_count >= MAX_ITERATIONS:
            return "create_bug"
        return "retry"
    return "validate"
```

### 5. Workflow Execution

```python
class TicketProcessingWorkflow:
    def __init__(self, github_token: Optional[str] = None):
        self.ticket_repo = TicketRepository()
        self.message_repo = MessageRepository()
        self.repository_repo = RepositoryRepository()
        self.git_service = GitService()
        self.ci_service = CIService()
        self.github_service = GitHubService(github_token) if github_token else None

        # Build and compile the StateGraph
        self.workflow = self._build_workflow()

    async def execute(self, ticket_id: str) -> TicketProcessingState:
        """Execute the workflow for a ticket"""
        initial_state = TicketProcessingState(ticket_id=ticket_id)

        # Run the StateGraph
        result = await self.workflow.ainvoke(initial_state)

        return result
```

---

## Workspace Management (Owner/Repo Structure)

### Problem

Avant : `/tmp/autocode-workspace/myapp`

- Conflit si deux owners ont un repo "myapp"

### Solution

Maintenant : `/tmp/autocode-workspace/owner/repo`

- Parse owner et repo depuis URL
- Support SSH et HTTPS

### Implementation

```python
def get_repo_path(self, repo_url: str) -> Path:
    """
    Get the local path for a repository.
    Creates structure: workspace_root/owner/repo

    Args:
        repo_url: Repository URL (SSH or HTTPS)

    Returns:
        Path to local repository

    Examples:
        https://github.com/joanix2/Auto-code-v1
          -> /tmp/autocode-workspace/joanix2/Auto-code-v1

        git@github.com:user1/myapp.git
          -> /tmp/autocode-workspace/user1/myapp
    """
    # Parse owner and repo from URL
    if repo_url.startswith("git@"):
        # SSH format: git@github.com:owner/repo.git
        match = re.search(r"git@[^:]+:([^/]+)/(.+?)(?:\.git)?$", repo_url)
    else:
        # HTTPS format: https://github.com/owner/repo
        match = re.search(r"https?://[^/]+/([^/]+)/(.+?)(?:\.git)?$", repo_url)

    if not match:
        raise ValueError(f"Could not parse owner/repo from URL: {repo_url}")

    owner = match.group(1)
    repo_name = match.group(2)

    # Create owner/repo structure
    repo_path = self.workspace_root / owner / repo_name
    repo_path.parent.mkdir(parents=True, exist_ok=True)

    return repo_path
```

### Benefits

✅ No conflicts between repos with same name
✅ Clear organization by owner
✅ Easy to find specific project
✅ Works with SSH and HTTPS URLs

### Examples

```python
# Different owners, same repo name
"https://github.com/user1/myapp"
  → /tmp/autocode-workspace/user1/myapp

"https://github.com/user2/myapp"
  → /tmp/autocode-workspace/user2/myapp

# SSH format
"git@github.com:joanix2/Auto-code-v1.git"
  → /tmp/autocode-workspace/joanix2/Auto-code-v1
```

---

## Comparison: Before vs After

### Before (Without LangGraph)

```python
async def process_ticket(self, ticket_id: str):
    # Manual state management
    ticket = get_ticket(ticket_id)

    # Manual iteration check
    if ticket.iteration_count >= MAX_ITERATIONS:
        create_bug_ticket(ticket)
        return

    # Manual repository prep
    repo_path = prepare_repository(ticket.repository_url)

    # Manual loop
    while True:
        # Manual iteration check again
        if ticket.iteration_count >= MAX_ITERATIONS:
            break

        # Call LLM
        llm_response = await call_llm(ticket)

        # Commit
        commit_changes(repo_path)

        # CI
        ci_result = run_ci(repo_path)

        # Manual decision logic
        if ci_result.failed:
            continue
        else:
            break

    # Manual final state
    ticket.status = "PENDING_VALIDATION"
```

**Problems**:

- Manual state management
- Duplicate iteration checks
- Hard to test individual steps
- No clear separation of concerns
- Difficult to visualize workflow
- No standard state machine semantics

### After (With LangGraph)

```python
class TicketProcessingWorkflow:
    def _build_workflow(self):
        workflow = StateGraph(TicketProcessingState)

        # Add nodes (clear separation)
        workflow.add_node("check_iterations", self._check_iterations)
        workflow.add_node("prepare_repository", self._prepare_repository)
        workflow.add_node("call_llm", self._call_llm)
        workflow.add_node("commit_changes", self._commit_changes)
        workflow.add_node("run_ci", self._run_ci)
        # ...

        # Add conditional edges (clear decision logic)
        workflow.add_conditional_edges(
            "check_iterations",
            self._should_continue_after_check,
            {"continue": "prepare_repository", "create_bug": "create_bug_ticket"}
        )

        return workflow.compile()

    async def execute(self, ticket_id: str):
        initial_state = TicketProcessingState(ticket_id=ticket_id)
        result = await self.workflow.ainvoke(initial_state)
        return result
```

**Benefits**:
✅ **State machine semantics** - Standard LangGraph patterns
✅ **Clear separation** - Each node is isolated and testable
✅ **Declarative edges** - Decision logic is explicit
✅ **Type safety** - Pydantic state model
✅ **Visualizable** - Can generate graph diagrams
✅ **Debuggable** - Track state at each node
✅ **Maintainable** - Easy to add/modify nodes

---

## Testing Strategy

### Unit Tests (Per Node)

```python
async def test_check_iterations_node():
    workflow = TicketProcessingWorkflow()

    # Test with iterations < MAX
    state = TicketProcessingState(
        ticket_id="test",
        iteration_count=2
    )
    result = await workflow._check_iterations(state)
    assert result.ticket is not None

    # Test with iterations >= MAX
    state = TicketProcessingState(
        ticket_id="test",
        iteration_count=5
    )
    result = await workflow._check_iterations(state)
    # Should have loaded ticket for bug creation
```

### Integration Tests (Full Workflow)

```python
async def test_full_workflow_success():
    workflow = TicketProcessingWorkflow()

    result = await workflow.execute("test-ticket-id")

    assert result.status == "PENDING_VALIDATION"
    assert result.ci_result.success is True
    assert len(result.conversation) > 0
```

### Decision Function Tests

```python
def test_should_retry_or_validate():
    workflow = TicketProcessingWorkflow()

    # Test retry (CI failed, iterations < MAX)
    state = TicketProcessingState(
        iteration_count=2,
        ci_result=CIResult(failed=True)
    )
    decision = workflow._should_retry_or_validate(state)
    assert decision == "retry"

    # Test validate (CI passed)
    state = TicketProcessingState(
        iteration_count=2,
        ci_result=CIResult(success=True)
    )
    decision = workflow._should_retry_or_validate(state)
    assert decision == "validate"

    # Test create_bug (CI failed, iterations >= MAX)
    state = TicketProcessingState(
        iteration_count=5,
        ci_result=CIResult(failed=True)
    )
    decision = workflow._should_retry_or_validate(state)
    assert decision == "create_bug"
```

---

## Performance Considerations

### State Size

- Pydantic model validation on each transition
- Keep state minimal (use IDs instead of full objects when possible)
- Consider lazy loading for large objects

### Async Execution

- All nodes are async
- Can run multiple tickets in parallel
- Use connection pooling for DB

### Checkpointing (Future)

LangGraph supports checkpointing for long-running workflows:

```python
workflow = StateGraph(TicketProcessingState)
# ... build workflow ...

# Add checkpointer
from langgraph.checkpoint import MemorySaver
checkpointer = MemorySaver()

compiled_workflow = workflow.compile(checkpointer=checkpointer)
```

---

## Monitoring & Observability

### Logging

Each node logs its actions:

```python
async def _check_iterations(self, state: TicketProcessingState):
    logger.info(f"Checking iterations for ticket {state.ticket_id}")
    # ...
    logger.info(f"Iteration count: {ticket.iteration_count}/{MAX_ITERATIONS}")
```

### Metrics

Track:

- Node execution time
- Iteration counts
- CI success/failure rates
- LLM token usage
- Workflow completion rate

### Tracing

Can integrate with OpenTelemetry for distributed tracing.

---

## Future Enhancements

### 1. Parallel Branches

```python
# Run CI and static analysis in parallel
workflow.add_node("run_ci", self._run_ci)
workflow.add_node("run_static_analysis", self._run_static_analysis)

workflow.add_edge("commit_changes", "run_ci")
workflow.add_edge("commit_changes", "run_static_analysis")

# Merge results
workflow.add_node("merge_results", self._merge_results)
workflow.add_edge("run_ci", "merge_results")
workflow.add_edge("run_static_analysis", "merge_results")
```

### 2. Human-in-the-Loop

```python
# Wait for human approval before PR
workflow.add_node("request_approval", self._request_approval)
workflow.add_conditional_edges(
    "request_approval",
    lambda state: "approved" if state.human_approved else "rejected"
)
```

### 3. Multi-Agent Orchestration

```python
# Different agents for different steps
workflow.add_node("analyze_agent", self._call_analyze_agent)
workflow.add_node("code_agent", self._call_code_agent)
workflow.add_node("review_agent", self._call_review_agent)
```

---

## Conclusion

✅ **LangGraph is now fully integrated** for the entire workflow  
✅ **Workspace structure improved** with owner/repo organization  
✅ **State machine semantics** for better maintainability  
✅ **Clear separation of concerns** with isolated nodes  
✅ **Type-safe state** with Pydantic models  
✅ **Testable and debuggable** architecture

The implementation follows best practices for state machine workflows and provides a solid foundation for future enhancements.
