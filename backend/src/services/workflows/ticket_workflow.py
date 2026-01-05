"""
Ticket Processing Workflow with LangGraph
Complete state machine for autonomous ticket development
"""

import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from ...models.ticket import Ticket
from ...models.message import Message
from ...repositories.ticket_repository import TicketRepository
from ...repositories.message_repository import MessageRepository
from ...repositories.repository_repository import RepositoryRepository
from ..git.git_service import GitService
from ..ci.ci_service import CIService, CIResult
from ..file_modification_service import FileModificationService
from ..agent.claude_agent import ClaudeAgent
from ..websocket.connection_manager import manager

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 10


class TicketProcessingState(BaseModel):
    """State for ticket processing workflow"""
    # Ticket info
    ticket_id: str
    ticket: Optional[Dict[str, Any]] = None
    repository: Optional[Dict[str, Any]] = None
    
    # Processing state
    status: str = "initialized"  # initialized, preparing, reasoning, testing, validation, completed, failed
    iteration_count: int = 0
    
    # Paths
    repo_path: Optional[str] = None
    branch_name: Optional[str] = None
    
    # Conversation
    messages: list = Field(default_factory=list)
    last_message: Optional[Dict[str, Any]] = None
    
    # Results
    llm_response: Optional[Dict[str, Any]] = None
    ci_result: Optional[Dict[str, Any]] = None
    commit_hash: Optional[str] = None
    
    # Errors
    errors: list = Field(default_factory=list)
    
    # Final result
    success: bool = False
    final_status: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class TicketProcessingWorkflow:
    """
    LangGraph-based workflow for complete ticket processing
    
    Workflow stages:
    1. check_iterations -> Check if MAX_ITERATIONS exceeded
    2. prepare_repository -> Clone/pull, setup branch
    3. load_conversation -> Get or create messages
    4. call_llm -> Reasoning and code generation
    5. commit_changes -> Git commit
    6. run_ci -> Execute tests
    7. handle_ci_result -> Check if CI passed/failed
    8. await_validation -> Set to PENDING_VALIDATION
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize workflow
        
        Args:
            github_token: GitHub token for API access
        """
        self.git_service = GitService()
        self.ci_service = CIService(github_token)
        
        self.ticket_repo = TicketRepository()
        self.message_repo = MessageRepository()
        self.repository_repo = RepositoryRepository()
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the complete LangGraph state machine
        
        Returns:
            Compiled StateGraph
        """
        workflow = StateGraph(TicketProcessingState)
        
        # Add all workflow nodes
        workflow.add_node("check_iterations", self._check_iterations)
        workflow.add_node("prepare_repository", self._prepare_repository)
        workflow.add_node("load_conversation", self._load_conversation)
        workflow.add_node("call_llm", self._call_llm)
        workflow.add_node("commit_changes", self._commit_changes)
        workflow.add_node("run_ci", self._run_ci)
        workflow.add_node("handle_ci_result", self._handle_ci_result)
        workflow.add_node("await_validation", self._await_validation)
        workflow.add_node("create_bug_ticket", self._create_bug_ticket)
        
        # Set entry point
        workflow.set_entry_point("check_iterations")
        
        # Define workflow edges
        
        # From check_iterations
        workflow.add_conditional_edges(
            "check_iterations",
            self._should_continue_after_check,
            {
                "prepare_repository": "prepare_repository",
                "create_bug_ticket": "create_bug_ticket"
            }
        )
        
        # Linear flow for preparation
        workflow.add_edge("prepare_repository", "load_conversation")
        workflow.add_edge("load_conversation", "call_llm")
        
        # From LLM to commit
        workflow.add_conditional_edges(
            "call_llm",
            self._should_commit,
            {
                "commit_changes": "commit_changes",
                "create_bug_ticket": "create_bug_ticket",
                END: END
            }
        )
        
        # From commit to CI
        workflow.add_edge("commit_changes", "run_ci")
        workflow.add_edge("run_ci", "handle_ci_result")
        
        # From CI result - decision point
        workflow.add_conditional_edges(
            "handle_ci_result",
            self._should_retry_or_validate,
            {
                "check_iterations": "check_iterations",  # Retry loop
                "await_validation": "await_validation",  # Success
                "create_bug_ticket": "create_bug_ticket"  # Max iterations
            }
        )
        
        # Terminal nodes
        workflow.add_edge("await_validation", END)
        workflow.add_edge("create_bug_ticket", END)
        
        return workflow.compile()
    
    # Node implementations
    
    def _check_iterations(self, state: TicketProcessingState) -> TicketProcessingState:
        """Check if MAX_ITERATIONS exceeded"""
        logger.info("=" * 80)
        logger.info(f"🔄 [WORKFLOW] Checking iterations for ticket {state.ticket_id}")
        logger.info(f"📊 Current iteration: {state.iteration_count}/{MAX_ITERATIONS}")
        logger.info("=" * 80)
        
        # Send WebSocket update
        import asyncio
        asyncio.create_task(manager.send_status_update(
            state.ticket_id,
            "IN_PROGRESS",
            "Vérification du nombre d'itérations...",
            step="check_iterations",
            progress=5
        ))
        
        # Load ticket if not already loaded
        if not state.ticket:
            ticket = self.ticket_repo.get_by_id(state.ticket_id)
            if not ticket:
                state.errors.append("Ticket not found")
                state.status = "failed"
                asyncio.create_task(manager.send_status_update(
                    state.ticket_id,
                    "FAILED",
                    "Ticket introuvable",
                    error="Ticket not found"
                ))
                return state
            
            state.ticket = {
                "id": ticket.id,
                "title": ticket.title,
                "description": ticket.description,
                "type": ticket.type,
                "priority": ticket.priority,
                "iteration_count": ticket.iteration_count,
                "repository_id": ticket.repository_id
            }
            state.iteration_count = ticket.iteration_count
        
        # Check limit
        if state.iteration_count >= MAX_ITERATIONS:
            logger.warning(f"Ticket {state.ticket_id} exceeded MAX_ITERATIONS ({MAX_ITERATIONS})")
            state.status = "cancelled"
            state.errors.append(f"Exceeded MAX_ITERATIONS ({MAX_ITERATIONS})")
            asyncio.create_task(manager.send_status_update(
                state.ticket_id,
                "CANCELLED",
                f"Limite d'itérations atteinte ({MAX_ITERATIONS})",
                error=f"MAX_ITERATIONS ({MAX_ITERATIONS}) exceeded"
            ))
            return state
        
        state.status = "preparing"
        asyncio.create_task(manager.send_status_update(
            state.ticket_id,
            "IN_PROGRESS",
            f"Itération {state.iteration_count + 1}/{MAX_ITERATIONS}",
            step="check_iterations",
            progress=10
        ))
        return state
    
    def _prepare_repository(self, state: TicketProcessingState) -> TicketProcessingState:
        """Prepare repository: clone/pull and setup branch"""
        logger.info("=" * 80)
        logger.info(f"📦 [GIT] Preparing repository for ticket {state.ticket_id}")
        logger.info(f"📁 Repository: {state.repository.get('name') if state.repository else 'Unknown'}")
        logger.info("=" * 80)
        
        import asyncio
        asyncio.create_task(manager.send_status_update(
            state.ticket_id,
            "IN_PROGRESS",
            "Préparation du repository...",
            step="prepare_repository",
            progress=20
        ))
        
        try:
            # Load repository info
            repository = self.repository_repo.get_repository_by_id(state.ticket["repository_id"])
            if not repository:
                raise ValueError("Repository not found")
            
            state.repository = {
                "id": repository.id,
                "url": repository.url,
                "name": repository.name
            }
            
            # Clone or pull
            if not self.git_service.is_cloned(repository.url):
                logger.info(f"Cloning repository {repository.url}")
                asyncio.create_task(manager.send_log(
                    state.ticket_id,
                    "INFO",
                    f"Clonage du repository {repository.name}..."
                ))
                repo_path = self.git_service.clone(repository.url)
            else:
                logger.info(f"Repository already cloned, pulling latest")
                asyncio.create_task(manager.send_log(
                    state.ticket_id,
                    "INFO",
                    f"Repository déjà cloné, pull des dernières modifications..."
                ))
                repo_path = self.git_service.get_repo_path(repository.url)
                self.git_service.pull(repository.url)
            
            state.repo_path = str(repo_path)
            
            # Create or checkout branch
            branch_name = f"ticket-{state.ticket_id[:8]}"
            state.branch_name = branch_name
            
            if not self.git_service.branch_exists(repository.url, branch_name):
                logger.info(f"Creating branch {branch_name}")
                asyncio.create_task(manager.send_log(
                    state.ticket_id,
                    "INFO",
                    f"Création de la branche {branch_name}..."
                ))
                self.git_service.create_branch(repository.url, branch_name)
            else:
                logger.info(f"Checking out existing branch {branch_name}")
                asyncio.create_task(manager.send_log(
                    state.ticket_id,
                    "INFO",
                    f"Checkout de la branche existante {branch_name}..."
                ))
                self.git_service.checkout_branch(repository.url, branch_name)
            
            # Rebase on main
            try:
                asyncio.create_task(manager.send_log(
                    state.ticket_id,
                    "INFO",
                    "Rebase sur la branche main..."
                ))
                self.git_service.rebase_branch(repository.url, branch_name, "main")
            except RuntimeError as e:
                logger.warning(f"Rebase failed: {e}, continuing anyway")
                asyncio.create_task(manager.send_log(
                    state.ticket_id,
                    "WARNING",
                    f"Rebase échoué: {e}, continuation quand même"
                ))
            
            state.status = "prepared"
            logger.info(f"Repository prepared at {state.repo_path}")
            asyncio.create_task(manager.send_status_update(
                state.ticket_id,
                "IN_PROGRESS",
                f"Repository préparé: {branch_name}",
                step="prepare_repository",
                progress=30
            ))
            
        except Exception as e:
            logger.error(f"Failed to prepare repository: {e}")
            state.status = "failed"
            state.errors.append(f"Repository preparation failed: {str(e)}")
            import asyncio
            asyncio.create_task(manager.send_status_update(
                state.ticket_id,
                "FAILED",
                "Échec de la préparation du repository",
                error=str(e)
            ))
        
        return state
    
    def _load_conversation(self, state: TicketProcessingState) -> TicketProcessingState:
        """Load or create conversation"""
        logger.info(f"Loading conversation for ticket {state.ticket_id}")
        
        # Get messages
        messages = self.message_repo.get_by_ticket_id(state.ticket_id)
        
        if not messages:
            # Create initial message from ticket
            logger.info("Creating initial message from ticket")
            content = f"""**New Ticket: {state.ticket['title']}**

**Type:** {state.ticket['type']}
**Priority:** {state.ticket['priority']}

**Description:**
{state.ticket['description']}

**Instructions:**
Please analyze this ticket and implement the required changes. Follow best practices and ensure code quality.
"""
            
            initial_message = Message(
                id="",
                ticket_id=state.ticket_id,
                role="user",
                content=content,
                step="ticket_description"
            )
            self.message_repo.create(initial_message)
            messages = [initial_message]
        
        # Store in state
        state.messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "step": msg.step,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
        
        state.last_message = state.messages[-1] if state.messages else None
        state.status = "ready_for_llm"
        
        return state
    
    def _call_llm(self, state: TicketProcessingState) -> TicketProcessingState:
        """Call LLM for reasoning and code generation, then apply modifications"""
        logger.info("=" * 80)
        logger.info(f"🤖 [CLAUDE] Calling LLM for ticket {state.ticket_id}")
        logger.info(f"💬 Messages in conversation: {len(state.messages)}")
        logger.info(f"🔄 Iteration: {state.iteration_count + 1}/{MAX_ITERATIONS}")
        logger.info("=" * 80)
        
        import asyncio
        asyncio.create_task(manager.send_status_update(
            state.ticket_id,
            "IN_PROGRESS",
            "Appel à Claude pour génération de code...",
            step="call_llm",
            progress=50
        ))
        
        try:
            agent = ClaudeAgent()
            
            # Run agent (analyze → generate → review)
            result = agent.run(
                ticket_id=state.ticket_id,
                ticket_title=state.ticket["title"],
                ticket_description=state.ticket["description"],
                ticket_type=state.ticket["type"],
                priority=state.ticket["priority"],
                repository_path=state.repo_path,
                repository_url=state.repository["url"],
                max_iterations=3
            )
            
            state.llm_response = result
            
            # ✅ APPLY FILE MODIFICATIONS using LangChain tools
            if result and result.get("final_output"):
                logger.info("📝 [FILES] Applying file modifications...")
                asyncio.create_task(manager.send_log(
                    state.ticket_id,
                    "INFO",
                    "Application des modifications de fichiers..."
                ))
                
                file_service = FileModificationService(state.repo_path)
                mod_results = file_service.apply_modifications(result["final_output"])
                
                if mod_results["success"]:
                    logger.info(f"✅ [FILES] Successfully modified {mod_results['succeeded']} file(s)")
                    if mod_results['failed'] > 0:
                        logger.warning(f"⚠️  [FILES] Failed to modify {mod_results['failed']} file(s)")
                    for file_path in mod_results.get('modified_files', []):
                        logger.info(f"  📄 Modified: {file_path}")
                    asyncio.create_task(manager.send_log(
                        state.ticket_id,
                        "INFO",
                        f"✅ {mod_results['succeeded']} fichier(s) modifié(s)"
                    ))
                    
                    # Get summary
                    summary = file_service.get_modified_files_summary(mod_results)
                    for line in summary.split("\n"):
                        if line.strip():
                            asyncio.create_task(manager.send_log(
                                state.ticket_id,
                                "INFO",
                                line
                            ))
                    
                    state.status = "code_applied"
                else:
                    logger.warning(f"File modifications partially failed: {mod_results.get('error')}")
                    asyncio.create_task(manager.send_log(
                        state.ticket_id,
                        "WARNING",
                        f"Modifications partiellement échouées: {mod_results.get('error')}"
                    ))
                    state.status = "code_generated"
            else:
                logger.warning("No file modifications found in LLM response")
                state.status = "code_generated"
            
            asyncio.create_task(manager.send_status_update(
                state.ticket_id,
                "IN_PROGRESS",
                "Code généré et appliqué",
                step="call_llm",
                progress=60
            ))
            
        except Exception as e:
            logger.error(f"LLM call or file modification failed: {e}", exc_info=True)
            state.status = "failed"
            state.errors.append(f"LLM/File modification failed: {str(e)}")
            import asyncio
            asyncio.create_task(manager.send_status_update(
                state.ticket_id,
                "FAILED",
                "Échec de la génération ou application du code",
                error=str(e)
            ))
        
        return state
    
    def _commit_changes(self, state: TicketProcessingState) -> TicketProcessingState:
        """Commit changes to Git"""
        logger.info("=" * 80)
        logger.info(f"💾 [GIT] Committing changes for ticket {state.ticket_id}")
        logger.info(f"🌿 Branch: {state.branch_name}")
        logger.info("=" * 80)
        
        try:
            if self.git_service.has_uncommitted_changes(state.repository["url"]):
                commit_message = f"feat(ticket-{state.ticket_id[:8]}): {state.ticket['title']}\n\nIteration {state.iteration_count + 1}"
                commit_hash = self.git_service.commit_changes(
                    state.repository["url"],
                    commit_message
                )
                state.commit_hash = commit_hash
                logger.info(f"✅ [GIT] Changes committed: {commit_hash}")
                logger.info(f"📝 [GIT] Commit message: {commit_message[:100]}...")
            else:
                logger.info("ℹ️  [GIT] No uncommitted changes to commit")
            
            state.status = "committed"
            
        except Exception as e:
            logger.error(f"Commit failed: {e}")
            state.errors.append(f"Commit failed: {str(e)}")
        
        return state
    
    def _run_ci(self, state: TicketProcessingState) -> TicketProcessingState:
        """Run CI/CD tests"""
        logger.info("=" * 80)
        logger.info(f"🧪 [CI/CD] Running tests for ticket {state.ticket_id}")
        logger.info(f"📦 Repository path: {state.repo_path}")
        logger.info(f"🔖 Commit: {state.commit_hash[:8] if state.commit_hash else 'No commit'}")
        logger.info("=" * 80)
        
        try:
            ci_result = self.ci_service.run_ci(
                self.git_service.get_repo_path(state.repository["url"]),
                state.commit_hash
            )
            
            state.ci_result = {
                "success": ci_result.success,
                "failed": ci_result.failed,
                "message": ci_result.message,
                "details": ci_result.details
            }
            
            if ci_result.success:
                logger.info(f"✅ [CI/CD] Tests passed successfully!")
            else:
                logger.error(f"❌ [CI/CD] Tests failed: {ci_result.message}")
                if ci_result.details:
                    logger.error(f"📋 [CI/CD] Details: {ci_result.details}")
            
            state.status = "ci_completed"
            
        except Exception as e:
            logger.error(f"CI execution failed: {e}")
            state.ci_result = {
                "success": False,
                "failed": True,
                "message": f"CI execution error: {str(e)}",
                "details": {}
            }
        
        return state
    
    def _handle_ci_result(self, state: TicketProcessingState) -> TicketProcessingState:
        """Handle CI result and increment iteration"""
        logger.info("=" * 80)
        logger.info(f"📊 [WORKFLOW] Handling CI result for ticket {state.ticket_id}")
        ci_success = state.ci_result.get("success", False) if state.ci_result else False
        logger.info(f"🧪 CI Status: {'✅ PASSED' if ci_success else '❌ FAILED'}")
        logger.info("=" * 80)
        
        # Increment iteration count
        state.iteration_count += 1
        
        # Update ticket in DB
        ticket = self.ticket_repo.get_by_id(state.ticket_id)
        ticket.iteration_count = state.iteration_count
        self.ticket_repo.update(ticket)
        
        if state.ci_result["failed"]:
            logger.warning(f"CI failed for ticket {state.ticket_id}")
            
            # Create error message for LLM
            error_content = self.ci_service.create_ci_error_message(
                CIResult(
                    success=False,
                    message=state.ci_result["message"],
                    details=state.ci_result["details"]
                )
            )
            
            error_message = Message(
                id="",
                ticket_id=state.ticket_id,
                role="system",
                content=error_content,
                step="ci_error"
            )
            self.message_repo.create(error_message)
            
            state.status = "ci_failed"
        else:
            logger.info(f"CI passed for ticket {state.ticket_id}")
            state.status = "ci_passed"
        
        return state
    
    def _await_validation(self, state: TicketProcessingState) -> TicketProcessingState:
        """Set ticket to PENDING_VALIDATION"""
        logger.info(f"Setting ticket {state.ticket_id} to PENDING_VALIDATION")
        
        # Update ticket status
        ticket = self.ticket_repo.get_by_id(state.ticket_id)
        ticket.status = "PENDING_VALIDATION"
        self.ticket_repo.update(ticket)
        
        state.status = "completed"
        state.success = True
        state.final_status = "PENDING_VALIDATION"
        
        return state
    
    def _create_bug_ticket(self, state: TicketProcessingState) -> TicketProcessingState:
        """Create bug ticket and cancel original"""
        logger.info(f"Creating bug ticket for failed ticket {state.ticket_id}")
        
        # Update original ticket
        ticket = self.ticket_repo.get_by_id(state.ticket_id)
        ticket.status = "CANCELLED"
        self.ticket_repo.update(ticket)
        
        # Create bug ticket
        bug_ticket = Ticket(
            id="",
            title=f"[BUG] Failed to process: {state.ticket['title']}",
            description=f"""Original ticket ({state.ticket_id}) failed after {state.iteration_count} iterations.

**Original Ticket:**
- Title: {state.ticket['title']}
- Type: {state.ticket['type']}
- Priority: {state.ticket['priority']}

**Reason:**
Maximum iterations ({MAX_ITERATIONS}) exceeded without successful completion.

**Errors:**
{chr(10).join('- ' + error for error in state.errors)}

**Action Required:**
Manual investigation needed to determine why the automated process failed.
""",
            type="bugfix",
            priority="high",
            status="OPEN",
            repository_id=state.ticket["repository_id"],
            order=0,
            iteration_count=0
        )
        
        created_bug = self.ticket_repo.create(bug_ticket, state.ticket["repository_id"])
        logger.info(f"Created bug ticket {created_bug.id}")
        
        state.status = "cancelled"
        state.final_status = "CANCELLED"
        
        return state
    
    # Decision functions
    
    def _should_continue_after_check(self, state: TicketProcessingState) -> Literal["prepare_repository", "create_bug_ticket"]:
        """Decide whether to continue or create bug ticket"""
        if state.status == "cancelled":
            return "create_bug_ticket"
        return "prepare_repository"
    
    def _should_commit(self, state: TicketProcessingState) -> Literal["commit_changes", "create_bug_ticket", "END"]:
        """Decide whether to commit changes"""
        if state.status == "failed":
            return "create_bug_ticket"
        elif state.status == "code_generated":
            return "commit_changes"
        return END
    
    def _should_retry_or_validate(self, state: TicketProcessingState) -> Literal["check_iterations", "await_validation", "create_bug_ticket"]:
        """Decide whether to retry, validate, or fail"""
        if state.status == "ci_failed":
            # Check if we can retry
            if state.iteration_count >= MAX_ITERATIONS:
                return "create_bug_ticket"
            return "check_iterations"  # Retry loop
        elif state.status == "ci_passed":
            return "await_validation"
        return "create_bug_ticket"
    
    async def execute(self, ticket_id: str) -> Dict[str, Any]:
        """
        Execute the complete workflow for a ticket
        
        Args:
            ticket_id: ID of the ticket to process
            
        Returns:
            Final state dictionary
        """
        logger.info("=" * 100)
        logger.info("🚀 " + "=" * 96)
        logger.info(f"🚀 STARTING LANGGRAPH WORKFLOW FOR TICKET: {ticket_id}")
        logger.info("🚀 " + "=" * 96)
        logger.info("=" * 100)
        
        # Initialize state
        initial_state = TicketProcessingState(ticket_id=ticket_id)
        
        # Run the workflow
        logger.info(f"⚙️  Initializing workflow state for ticket {ticket_id}")
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info("=" * 100)
        logger.info("🏁 " + "=" * 96)
        logger.info(f"🏁 WORKFLOW COMPLETED FOR TICKET: {ticket_id}")
        logger.info(f"✅ Success: {final_state.success}")
        logger.info(f"📊 Status: {final_state.final_status}")
        logger.info(f"🔄 Iterations: {final_state.iteration_count}/{MAX_ITERATIONS}")
        logger.info(f"❌ Errors: {len(final_state.errors)}")
        logger.info("🏁 " + "=" * 96)
        logger.info("=" * 100)
        
        # Return result
        return {
            "success": final_state.success,
            "status": final_state.final_status,
            "iterations": final_state.iteration_count,
            "errors": final_state.errors,
            "commit_hash": final_state.commit_hash,
            "ci_result": final_state.ci_result
        }
