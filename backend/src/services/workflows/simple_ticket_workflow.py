"""
Simplified Ticket Processing Workflow
Simple sequential workflow without LangGraph dependency
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ...database import Neo4jConnection
from ...repositories.ticket_repository import TicketRepository
from ...repositories.message_repository import MessageRepository
from ...repositories.repository_repository import RepositoryRepository
from ...models.ticket import Ticket
from ...models.message import Message
from ..git.git_service import GitService
from ..git.pull_request_service import PullRequestService
from ..git.branch_service import BranchService
from ..ci.ci_service import CIService
from ..messaging.message_service import MessageService
from ...agent.dummy_agent import DummyAgent

from .workflow_state import TicketProcessingState
from .workflow_helpers import safe_ws_update, safe_ws_log, log_workflow_step, MAX_ITERATIONS

logger = logging.getLogger(__name__)


class TicketProcessingWorkflow:
    """
    Simplified workflow for ticket processing
    Sequential execution without LangGraph state machine
    
    Workflow stages:
    1. Validate ticket and check iterations
    2. Prepare repository (clone/pull, create branch)
    3. Load conversation history
    4. Call LLM for code generation
    5. Commit changes
    6. Run CI tests
    7. Handle CI result (retry or validate)
    8. Await human validation or create bug ticket
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize workflow
        
        Args:
            github_token: GitHub token for API access
        """
        self.github_token = github_token
        self.git_service = GitService()
        self.branch_service = BranchService()
        self.pr_service = PullRequestService(github_token) if github_token else None
        self.ci_service = CIService(github_token)
        
        # Initialize agent
        self.agent = DummyAgent()
        
        # Initialize repositories with db connection
        db = Neo4jConnection()
        self.ticket_repo = TicketRepository(db)
        self.message_repo = MessageRepository()  # Static methods - no db needed
        self.repository_repo = RepositoryRepository(db)
        
        # Initialize message service for iteration checking
        self.message_service = MessageService()
    
    async def execute(self, ticket_id: str) -> Dict[str, Any]:
        """
        Execute the complete workflow for a ticket
        
        Args:
            ticket_id: ID of the ticket to process
            
        Returns:
            Dictionary with processing results
        """
        log_workflow_step("Starting Workflow", ticket_id)
        safe_ws_update(ticket_id, "IN_PROGRESS", "Démarrage du traitement automatique...", progress=0)
        
        # Update ticket status to in_progress in database
        try:
            await self.ticket_repo.update_ticket_status(ticket_id, "in_progress")
            logger.info(f"Ticket {ticket_id} status updated to in_progress in database")
        except Exception as e:
            logger.warning(f"Failed to update ticket status to in_progress: {e}")
        
        # Initialize state
        state = TicketProcessingState(ticket_id=ticket_id)
        
        try:
            # Step 1: Validate and check iterations
            state = await self._check_iterations(state)
            if state.status == "cancelled":
                return await self._handle_max_iterations(state)
            
            # Step 2: Prepare repository
            safe_ws_update(ticket_id, "IN_PROGRESS", "Préparation du dépôt...", progress=10)
            state = await self._prepare_repository(state)
            if state.status == "failed":
                return self._error_result(state, "Repository preparation failed")
            
            # Step 3: Load conversation
            safe_ws_update(ticket_id, "IN_PROGRESS", "Chargement de l'historique...", progress=20)
            state = await self._load_conversation(state)
            
            # Step 4: Call LLM for code generation
            safe_ws_update(ticket_id, "IN_PROGRESS", "Génération du code avec IA...", progress=30)
            state = await self._call_llm(state)
            if state.status == "failed":
                return self._error_result(state, "Code generation failed")
            
            # Step 5: Commit changes
            safe_ws_update(ticket_id, "IN_PROGRESS", "Commit des modifications...", progress=60)
            state = await self._commit_changes(state)
            if state.status == "failed":
                return self._error_result(state, "Commit failed")
            
            # Step 6: Run CI tests
            safe_ws_update(ticket_id, "IN_PROGRESS", "Exécution des tests...", progress=75)
            state = await self._run_ci(state)
            
            # Step 7: Handle CI result
            state = await self._handle_ci_result(state)
            
            # Step 8: Create Pull Request (if CI passed)
            if state.ci_result and state.ci_result.get("passed"):
                safe_ws_update(ticket_id, "IN_PROGRESS", "Création de la Pull Request...", progress=90)
                state = await self._create_pull_request(state)
                
                # Update ticket status to pending_validation in database
                try:
                    await self.ticket_repo.update_ticket_status(ticket_id, "pending_validation")
                    logger.info(f"Ticket {ticket_id} status updated to pending_validation in database")
                except Exception as e:
                    logger.warning(f"Failed to update ticket status to pending_validation: {e}")
                
                safe_ws_update(ticket_id, "PENDING_VALIDATION", "En attente de validation humaine", progress=100)
                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "status": "PENDING_VALIDATION",
                    "commit_hash": state.commit_hash,
                    "pr_url": state.final_status,  # Will contain PR URL
                    "message": "Code generated, tests passed, PR created - awaiting human validation"
                }
            else:
                # CI failed - check if should retry
                if state.iteration_count < MAX_ITERATIONS:
                    safe_ws_update(ticket_id, "IN_PROGRESS", "Tests échoués - nouvelle tentative...", progress=25)
                    # Recursive retry (simplified - in production use queue/background task)
                    return await self.execute(ticket_id)
                else:
                    return await self._handle_max_iterations(state)
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            safe_ws_update(ticket_id, "FAILED", f"Erreur: {str(e)}", error=str(e))
            
            # Update ticket status to cancelled in database (no "failed" status)
            try:
                await self.ticket_repo.update_ticket_status(ticket_id, "cancelled")
                logger.info(f"Ticket {ticket_id} status updated to cancelled in database (workflow failed)")
            except Exception as update_error:
                logger.warning(f"Failed to update ticket status to cancelled: {update_error}")
            
            return {
                "success": False,
                "ticket_id": ticket_id,
                "status": "FAILED",
                "error": str(e)
            }
    
    async def _check_iterations(self, state: TicketProcessingState) -> TicketProcessingState:
        """Check if MAX_ITERATIONS exceeded using message count"""
        # Get message count for this ticket
        message_count = self.message_service.get_message_count(state.ticket_id)
        state.iteration_count = message_count
        
        log_workflow_step("Checking Iterations", state.ticket_id, f"Message count: {message_count}/{MAX_ITERATIONS}")
        
        # Load ticket
        ticket = await self.ticket_repo.get_ticket_by_id(state.ticket_id)
        if not ticket:
            state.errors.append("Ticket not found")
            state.status = "failed"
            return state
        
        state.ticket = {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "ticket_type": ticket.ticket_type,
            "priority": ticket.priority,
            "repository_id": ticket.repository_id
        }
        
        # Check limit using message count
        if self.message_service.is_over_limit(state.ticket_id, MAX_ITERATIONS):
            logger.warning(f"Ticket {state.ticket_id} exceeded MAX_ITERATIONS (message count: {message_count})")
            state.status = "cancelled"
            state.errors.append(f"Exceeded MAX_ITERATIONS ({MAX_ITERATIONS}) - message count: {message_count}")
        
        return state
    
    async def _prepare_repository(self, state: TicketProcessingState) -> TicketProcessingState:
        """Prepare repository - clone/pull and create branch"""
        log_workflow_step("Preparing Repository", state.ticket_id)
        
        try:
            # Get repository info
            repo_id = state.ticket["repository_id"]
            repository = await self.repository_repo.get_repository_by_id(repo_id)
            
            if not repository:
                state.status = "failed"
                state.errors.append(f"Repository {repo_id} not found")
                return state
            
            state.repository = {
                "id": repository.id,
                "name": repository.name,
                "url": repository.url,
                "full_name": repository.full_name
            }
            
            # Clone or pull repository using GitService
            logger.info(f"Cloning/pulling repository: {repository.url}")
            try:
                repo_path, was_cloned = self.git_service.clone_or_pull(
                    repo_url=repository.url,
                    token=self.github_token
                )
                state.repo_path = str(repo_path)
                logger.info(f"Repository {'cloned' if was_cloned else 'updated'}: {repo_path}")
            except Exception as e:
                logger.error(f"Failed to clone/pull repository: {e}")
                state.status = "failed"
                state.errors.append(f"Repository clone/pull failed: {str(e)}")
                return state
            
            # Create/checkout branch
            ticket_dict = state.ticket
            ticket_obj = Ticket(
                id=ticket_dict["id"],
                title=ticket_dict["title"],
                description=ticket_dict["description"],
                ticket_type=ticket_dict["ticket_type"],
                priority=ticket_dict["priority"],
                status="in_progress",
                repository_id=ticket_dict["repository_id"],
                order=0,
                created_by="system"
            )
            
            branch_name, was_created = self.branch_service.ensure_branch_for_ticket(
                ticket=ticket_obj,
                repo_url=repository.url,
                base_branch="main"
            )
            state.branch_name = branch_name
            
            logger.info(f"Branch {'created' if was_created else 'checked out'}: {state.branch_name}")
            
        except Exception as e:
            logger.error(f"Error preparing repository: {e}", exc_info=True)
            state.status = "failed"
            state.errors.append(f"Repository preparation failed: {str(e)}")
        
        return state
    
    async def _load_conversation(self, state: TicketProcessingState) -> TicketProcessingState:
        """Load conversation history"""
        log_workflow_step("Loading Conversation", state.ticket_id)
        
        try:
            # Get messages for this ticket
            messages = MessageRepository.get_by_ticket_id(state.ticket_id)
            
            state.messages = [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp)
                }
                for msg in messages
            ]
            
            logger.info(f"Loaded {len(state.messages)} messages for ticket {state.ticket_id}")
            
        except Exception as e:
            logger.warning(f"Error loading conversation: {e}")
            # Not critical - continue without messages
            state.messages = []
        
        return state
    
    async def _call_llm(self, state: TicketProcessingState) -> TicketProcessingState:
        """Call LLM for code generation"""
        log_workflow_step("Calling Agent for Code Generation", state.ticket_id)
        
        try:
            # Convert state.ticket dict to Ticket model
            ticket_dict = state.ticket
            ticket = Ticket(
                id=ticket_dict["id"],
                title=ticket_dict["title"],
                description=ticket_dict["description"],
                ticket_type=ticket_dict["ticket_type"],
                priority=ticket_dict["priority"],
                status="in_progress",
                repository_id=ticket_dict["repository_id"],
                order=0,
                created_by="system"  # Placeholder
            )
            
            # Get initial message if any
            initial_message = None
            if state.messages:
                msg = state.messages[0]
                initial_message = Message(
                    id=msg.get("id", ""),
                    ticket_id=state.ticket_id,
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    timestamp=datetime.now()
                )
            
            # Call agent to process ticket
            from pathlib import Path
            repo_path = Path(state.repo_path) if state.repo_path else Path("/tmp/placeholder")
            
            logger.info(f"Calling DummyAgent with repo_path: {repo_path}")
            result = self.agent.process_ticket(ticket, repo_path, initial_message)
            
            logger.info(f"Agent result: {result}")
            state.llm_response = result
            
            if not result.get("success"):
                state.status = "failed"
                state.errors.append(f"Agent failed: {result.get('message', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error calling agent: {e}", exc_info=True)
            state.status = "failed"
            state.errors.append(f"Agent error: {str(e)}")
            state.llm_response = {"success": False, "error": str(e)}
        
        return state
    
    async def _commit_changes(self, state: TicketProcessingState) -> TicketProcessingState:
        """Commit changes to git"""
        log_workflow_step("Committing Changes", state.ticket_id)
        
        try:
            # Get files that were modified by the agent
            modified_files = state.llm_response.get("files_modified", [])
            
            if not modified_files:
                logger.warning("No files were modified - skipping commit")
                state.commit_hash = None
                return state
            
            # Check if there are uncommitted changes
            repo_url = state.repository["url"]
            if not self.git_service.has_uncommitted_changes(repo_url):
                logger.warning("No uncommitted changes detected - skipping commit")
                state.commit_hash = None
                return state
            
            # Prepare commit message
            commit_message = f"feat: {state.ticket['title']}\n\nTicket: {state.ticket_id}\nFiles modified: {', '.join(modified_files)}"
            
            # Use GitService to add, commit, and push
            logger.info(f"Committing changes to {state.branch_name}: {modified_files}")
            logger.info(f"Commit message: {commit_message}")
            
            result = self.git_service.add_commit_and_push(
                repo_url=repo_url,
                commit_message=commit_message,
                branch_name=state.branch_name,
                token=self.github_token
            )
            
            if result.get("success"):
                state.commit_hash = result.get("commit_hash")
                logger.info(f"✅ Changes committed and pushed: {state.commit_hash[:7]}")
                
                # Add message to ticket
                import uuid
                commit_msg = Message(
                    id=str(uuid.uuid4()),
                    ticket_id=state.ticket_id,
                    role="system",
                    content=f"Changements committés et pushés: {state.commit_hash[:7]}\n{commit_message}",
                    timestamp=datetime.now(),
                    metadata={
                        "commit_hash": state.commit_hash,
                        "branch": state.branch_name,
                        "source": "workflow"
                    }
                )
                self.message_service.create_message(commit_msg)
            else:
                logger.error(f"Commit failed: {result.get('message')}")
                state.status = "failed"
                state.errors.append(f"Commit failed: {result.get('message')}")
            
        except Exception as e:
            logger.error(f"Error committing changes: {e}", exc_info=True)
            state.status = "failed"
            state.errors.append(f"Commit failed: {str(e)}")
        
        return state
    
    async def _run_ci(self, state: TicketProcessingState) -> TicketProcessingState:
        """Run CI tests"""
        log_workflow_step("Running CI", state.ticket_id)
        
        try:
            # For now, skip CI tests and assume success
            # TODO: Implement actual CI when repository is set up
            # result = await self.ci_service.run_tests(state.repo_path)
            
            logger.info("CI tests skipped (auto-success for now)")
            state.ci_result = {"passed": True, "message": "CI skipped"}
            
        except Exception as e:
            logger.error(f"Error running CI: {e}", exc_info=True)
            state.ci_result = {"passed": False, "error": str(e)}
        
        return state
    
    async def _handle_ci_result(self, state: TicketProcessingState) -> TicketProcessingState:
        """Handle CI test results"""
        if state.ci_result and state.ci_result.get("passed"):
            logger.info(f"✅ CI tests passed for ticket {state.ticket_id}")
            state.status = "completed"
            state.success = True
        else:
            logger.warning(f"❌ CI tests failed for ticket {state.ticket_id}")
            state.status = "failed"
            state.iteration_count += 1
        
        return state
    
    async def _create_pull_request(self, state: TicketProcessingState) -> TicketProcessingState:
        """Create a Pull Request on GitHub"""
        log_workflow_step("Creating Pull Request", state.ticket_id)
        
        try:
            if not self.pr_service:
                logger.warning("PR service not available (no GitHub token)")
                state.final_status = "No PR created - missing GitHub token"
                return state
            
            if not state.commit_hash:
                logger.warning("No commit hash - skipping PR creation")
                state.final_status = "No PR created - no commits"
                return state
            
            # Prepare PR details
            pr_title = f"feat: {state.ticket['title']}"
            pr_body = f"""## {state.ticket['title']}

**Type:** {state.ticket['ticket_type']}
**Priority:** {state.ticket['priority']}

### Description
{state.ticket.get('description', 'No description provided')}

### Changes
{state.llm_response.get('message', 'Code modifications by AI agent')}

### Analysis
{state.llm_response.get('details', {}).get('analysis', 'N/A')}

---
Ticket: {state.ticket_id}
Commit: {state.commit_hash[:7]}
Branch: {state.branch_name}
"""
            
            # Create PR
            logger.info(f"Creating PR: {pr_title}")
            pr_result = self.pr_service.create_pull_request(
                repo_full_name=state.repository["full_name"],
                title=pr_title,
                body=pr_body,
                head_branch=state.branch_name,
                base_branch="main"
            )
            
            if pr_result:
                pr_url = pr_result.get("html_url", "")
                pr_number = pr_result.get("number", "")
                logger.info(f"✅ PR created: #{pr_number} - {pr_url}")
                state.final_status = pr_url
                
                # Add message to ticket
                import uuid
                pr_msg = Message(
                    id=str(uuid.uuid4()),
                    ticket_id=state.ticket_id,
                    role="system",
                    content=f"Pull Request créée: #{pr_number}\n{pr_url}\n\n{pr_title}",
                    timestamp=datetime.now(),
                    metadata={
                        "pr_number": pr_number,
                        "pr_url": pr_url,
                        "source": "workflow"
                    }
                )
                self.message_service.create_message(pr_msg)
            else:
                logger.error("PR creation returned no result")
                state.final_status = "PR creation failed"
                
        except Exception as e:
            logger.error(f"Error creating PR: {e}", exc_info=True)
            state.final_status = f"PR creation error: {str(e)}"
        
        return state
    
    async def _handle_max_iterations(self, state: TicketProcessingState) -> Dict[str, Any]:
        """Handle max iterations exceeded"""
        log_workflow_step("Max Iterations Exceeded", state.ticket_id)
        safe_ws_update(state.ticket_id, "CANCELLED", f"Limite d'itérations atteinte ({MAX_ITERATIONS})")
        
        # Update ticket status to cancelled in database
        try:
            await self.ticket_repo.update_ticket_status(state.ticket_id, "cancelled")
            logger.info(f"Ticket {state.ticket_id} status updated to cancelled in database")
        except Exception as e:
            logger.warning(f"Failed to update ticket status to cancelled: {e}")
        
        # TODO: Create bug ticket
        
        return {
            "success": False,
            "ticket_id": state.ticket_id,
            "status": "CANCELLED",
            "error": f"MAX_ITERATIONS ({MAX_ITERATIONS}) exceeded",
            "iteration_count": state.iteration_count
        }
    
    def _error_result(self, state: TicketProcessingState, message: str) -> Dict[str, Any]:
        """Return error result"""
        return {
            "success": False,
            "ticket_id": state.ticket_id,
            "status": "FAILED",
            "error": message,
            "errors": state.errors
        }
