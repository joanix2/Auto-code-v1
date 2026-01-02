"""
Ticket Processing Service
Main workflow implementation for autonomous ticket development
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.ticket import Ticket
from ..models.message import Message
from ..repositories.ticket_repository import TicketRepository
from ..repositories.message_repository import MessageRepository
from ..repositories.repository_repository import RepositoryRepository
from ..repositories.user_repository import UserRepository
from ..services.git_service import GitService
from ..services.ci_service import CIService, CIResult
from ..agent.claude_agent import ClaudeAgent, AgentState
from .github_service import GitHubService

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 10


class TicketProcessingService:
    """
    Main service for processing tickets with LLM
    Implements the complete workflow from ticket to PR
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize ticket processing service
        
        Args:
            github_token: GitHub token for API access
        """
        self.git_service = GitService()
        self.ci_service = CIService(github_token)
        self.github_service = GitHubService(github_token) if github_token else None
        
        self.ticket_repo = TicketRepository()
        self.message_repo = MessageRepository()
        self.repository_repo = RepositoryRepository()
    
    async def process_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """
        Main entry point for ticket processing
        Implements the complete workflow
        
        Args:
            ticket_id: ID of the ticket to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Starting ticket processing for {ticket_id}")
        
        # Get ticket
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Get repository
        repository = self.repository_repo.get_repository_by_id(ticket.repository_id)
        if not repository:
            raise ValueError(f"Repository {ticket.repository_id} not found")
        
        # --- Security: Check iteration limit ---
        if ticket.iteration_count >= MAX_ITERATIONS:
            logger.warning(f"Ticket {ticket_id} exceeded max iterations ({MAX_ITERATIONS})")
            ticket.status = "CANCELLED"
            self.ticket_repo.update(ticket)
            
            # Create bug ticket
            self._create_bug_ticket(ticket, repository)
            
            return {
                "success": False,
                "status": "CANCELLED",
                "reason": "max_iterations_exceeded",
                "iterations": ticket.iteration_count
            }
        
        # --- Set ticket to PENDING ---
        ticket.status = "PENDING"
        self.ticket_repo.update(ticket)
        logger.info(f"Ticket {ticket_id} set to PENDING")
        
        # --- Prepare repository ---
        try:
            repo_path = self._prepare_repository(repository.url, ticket)
            logger.info(f"Repository prepared at {repo_path}")
        except Exception as e:
            logger.error(f"Failed to prepare repository: {e}")
            ticket.status = "CANCELLED"
            self.ticket_repo.update(ticket)
            return {
                "success": False,
                "status": "CANCELLED",
                "reason": "repository_preparation_failed",
                "error": str(e)
            }
        
        # --- Get or create conversation ---
        conversation = self.message_repo.get_by_ticket_id(ticket_id)
        
        if not conversation:
            # Create initial message from ticket
            initial_message = self._create_message_from_ticket(ticket)
            self.message_repo.create(initial_message)
            conversation = [initial_message]
            logger.info("Created initial message from ticket")
        else:
            logger.info(f"Retrieved conversation with {len(conversation)} messages")
        
        # Get last message
        last_message = conversation[-1] if conversation else None
        
        # --- Main processing loop ---
        result = await self._processing_loop(ticket, repository, repo_path, last_message)
        
        return result
    
    def _prepare_repository(self, repo_url: str, ticket: Ticket) -> str:
        """
        Prepare repository: clone/pull and setup branch
        
        Args:
            repo_url: Repository URL
            ticket: Ticket being processed
            
        Returns:
            Path to repository
        """
        # Clone or pull
        if not self.git_service.is_cloned(repo_url):
            logger.info(f"Cloning repository {repo_url}")
            repo_path = self.git_service.clone(repo_url)
        else:
            logger.info(f"Repository already cloned, pulling latest")
            repo_path = self.git_service.get_repo_path(repo_url)
            self.git_service.pull(repo_url)
        
        # Create or checkout branch
        branch_name = f"ticket-{ticket.id[:8]}"
        
        if not self.git_service.branch_exists(repo_url, branch_name):
            logger.info(f"Creating branch {branch_name}")
            self.git_service.create_branch(repo_url, branch_name)
        else:
            logger.info(f"Checking out existing branch {branch_name}")
            self.git_service.checkout_branch(repo_url, branch_name)
        
        # Rebase on main
        try:
            self.git_service.rebase_branch(repo_url, branch_name, "main")
        except RuntimeError as e:
            logger.warning(f"Rebase failed: {e}, continuing anyway")
        
        return str(repo_path)
    
    def _create_message_from_ticket(self, ticket: Ticket) -> Message:
        """
        Create initial LLM message from ticket description
        
        Args:
            ticket: Ticket object
            
        Returns:
            Message object
        """
        content = f"""**New Ticket: {ticket.title}**

**Type:** {ticket.type}
**Priority:** {ticket.priority}

**Description:**
{ticket.description}

**Instructions:**
Please analyze this ticket and implement the required changes. Follow best practices and ensure code quality.
"""
        
        return Message(
            id="",
            ticket_id=ticket.id,
            role="user",
            content=content,
            step="ticket_description"
        )
    
    async def _processing_loop(self, ticket: Ticket, repository: Any, 
                               repo_path: str, last_message: Optional[Message]) -> Dict[str, Any]:
        """
        Main processing loop with LLM reasoning
        
        Args:
            ticket: Ticket being processed
            repository: Repository object
            repo_path: Path to local repository
            last_message: Last message in conversation
            
        Returns:
            Processing result
        """
        agent = ClaudeAgent()
        iteration = 0
        
        while True:
            # Security check before LLM call
            if ticket.iteration_count >= MAX_ITERATIONS:
                logger.warning(f"Max iterations reached in loop for ticket {ticket.id}")
                ticket.status = "CANCELLED"
                self.ticket_repo.update(ticket)
                self._create_bug_ticket(ticket, repository)
                
                return {
                    "success": False,
                    "status": "CANCELLED",
                    "reason": "max_iterations_in_loop",
                    "iterations": ticket.iteration_count
                }
            
            logger.info(f"Processing iteration {iteration + 1} for ticket {ticket.id}")
            
            # --- Call LLM for reasoning and code generation ---
            try:
                llm_response = await self._call_llm(agent, ticket, repository, last_message)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                ticket.status = "CANCELLED"
                self.ticket_repo.update(ticket)
                return {
                    "success": False,
                    "status": "CANCELLED",
                    "reason": "llm_failed",
                    "error": str(e)
                }
            
            # --- Apply code modifications ---
            # Note: For now, the LLM generates code but doesn't apply it automatically
            # This would need integration with a code modification service
            logger.info("Code modifications generated by LLM")
            
            # --- Commit changes ---
            if self.git_service.has_uncommitted_changes(repository.url):
                try:
                    commit_hash = self.git_service.commit_changes(
                        repository.url,
                        f"feat(ticket-{ticket.id[:8]}): {ticket.title}\n\nIteration {iteration + 1}"
                    )
                    logger.info(f"Changes committed: {commit_hash}")
                except Exception as e:
                    logger.error(f"Commit failed: {e}")
                    # Continue anyway
            
            # --- Run CI ---
            ci_result = self.ci_service.run_ci(self.git_service.get_repo_path(repository.url))
            logger.info(f"CI result: {ci_result}")
            
            # Increment iteration count
            ticket.iteration_count += 1
            self.ticket_repo.update(ticket)
            iteration += 1
            
            # --- Handle CI failure ---
            if ci_result.failed:
                logger.warning(f"CI failed for ticket {ticket.id}")
                
                # Create error message
                error_message = Message(
                    id="",
                    ticket_id=ticket.id,
                    role="system",
                    content=self.ci_service.create_ci_error_message(ci_result),
                    step="ci_error"
                )
                self.message_repo.create(error_message)
                last_message = error_message
                
                # Continue loop to retry
                continue
            
            # --- CI Passed! ---
            logger.info(f"CI passed for ticket {ticket.id}")
            
            # Set ticket to VALIDATION
            ticket.status = "PENDING_VALIDATION"
            self.ticket_repo.update(ticket)
            
            # Wait for human validation
            # Note: This is async - human will validate via UI
            logger.info(f"Ticket {ticket.id} waiting for human validation")
            
            return {
                "success": True,
                "status": "PENDING_VALIDATION",
                "iterations": ticket.iteration_count,
                "message": "Code generated and CI passed, awaiting human validation"
            }
    
    async def _call_llm(self, agent: ClaudeAgent, ticket: Ticket, 
                       repository: Any, last_message: Optional[Message]) -> Dict[str, Any]:
        """
        Call LLM for reasoning and code generation
        
        Args:
            agent: Claude agent instance
            ticket: Ticket being processed
            repository: Repository object
            last_message: Last message in conversation
            
        Returns:
            LLM response
        """
        # Build context from conversation
        conversation = self.message_repo.get_by_ticket_id(ticket.id)
        
        # Run agent workflow
        result = await agent.run(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            ticket_description=ticket.description,
            ticket_type=ticket.type,
            priority=ticket.priority,
            repository_path=str(self.git_service.get_repo_path(repository.url)),
            repository_url=repository.url,
            max_iterations=3  # Limit iterations per LLM call
        )
        
        return result
    
    def _create_bug_ticket(self, original_ticket: Ticket, repository: Any) -> Ticket:
        """
        Create a bug ticket when original ticket fails
        
        Args:
            original_ticket: Ticket that failed
            repository: Repository object
            
        Returns:
            Created bug ticket
        """
        bug_ticket = Ticket(
            id="",
            title=f"[BUG] Failed to process: {original_ticket.title}",
            description=f"""Original ticket ({original_ticket.id}) failed after {original_ticket.iteration_count} iterations.

**Original Ticket:**
- Title: {original_ticket.title}
- Type: {original_ticket.type}
- Priority: {original_ticket.priority}

**Reason:**
Maximum iterations ({MAX_ITERATIONS}) exceeded without successful completion.

**Action Required:**
Manual investigation needed to determine why the automated process failed.
""",
            type="bugfix",
            priority="high",
            status="OPEN",
            repository_id=original_ticket.repository_id,
            order=0,
            iteration_count=0
        )
        
        created_bug = self.ticket_repo.create(bug_ticket, repository.id)
        logger.info(f"Created bug ticket {created_bug.id} for failed ticket {original_ticket.id}")
        
        return created_bug
    
    async def handle_validation_result(self, ticket_id: str, approved: bool, 
                                       feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle human validation result
        
        Args:
            ticket_id: Ticket ID
            approved: Whether the changes were approved
            feedback: Optional feedback from human
            
        Returns:
            Result dictionary
        """
        ticket = self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        repository = self.repository_repo.get_repository_by_id(ticket.repository_id)
        
        if approved:
            logger.info(f"Ticket {ticket_id} approved, creating PR")
            
            # Create Pull Request
            if self.github_service:
                try:
                    branch_name = f"ticket-{ticket.id[:8]}"
                    pr = self.github_service.create_pull_request(
                        repository.url,
                        title=ticket.title,
                        body=ticket.description,
                        head_branch=branch_name,
                        base_branch="main"
                    )
                    logger.info(f"Created PR: {pr}")
                except Exception as e:
                    logger.error(f"Failed to create PR: {e}")
            
            # Set ticket to CLOSED
            ticket.status = "CLOSED"
            self.ticket_repo.update(ticket)
            
            return {
                "success": True,
                "status": "CLOSED",
                "message": "Changes approved and PR created"
            }
        else:
            logger.info(f"Ticket {ticket_id} rejected")
            
            # Create rejection message
            if feedback:
                rejection_message = Message(
                    id="",
                    ticket_id=ticket_id,
                    role="user",
                    content=f"**Human Feedback (Rejected):**\n\n{feedback}\n\nPlease address the feedback and try again.",
                    step="human_feedback"
                )
                self.message_repo.create(rejection_message)
            
            # Set ticket back to OPEN
            ticket.status = "OPEN"
            self.ticket_repo.update(ticket)
            
            return {
                "success": True,
                "status": "OPEN",
                "message": "Changes rejected, ticket reopened for revision"
            }
