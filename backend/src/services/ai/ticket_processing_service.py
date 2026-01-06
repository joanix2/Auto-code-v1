"""
Ticket Processing Service
Main workflow implementation for autonomous ticket development
Uses LangGraph for state machine orchestration
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ...models.ticket import Ticket
from ...models.message import Message
from ...repositories.ticket_repository import TicketRepository
from ...repositories.message_repository import MessageRepository
from ...repositories.repository_repository import RepositoryRepository
from ...repositories.user_repository import UserRepository
from ..git.git_service import GitService
from ..git.github_service import GitHubService
from ..ci.ci_service import CIService, CIResult
from ..workflows.simple_ticket_workflow import TicketProcessingWorkflow  # Use simplified workflow
# from ...agent.claude_agent import ClaudeAgent, AgentState  # TODO: Fix LangGraph compatibility

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 10


class TicketProcessingService:
    """
    Main service for processing tickets with LLM
    Uses LangGraph workflow for state machine orchestration
    Implements the complete workflow from ticket to PR
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize ticket processing service
        
        Args:
            github_token: GitHub token for API access
        """
        from ...database import Neo4jConnection
        
        self.workflow = TicketProcessingWorkflow(github_token)
        self.git_service = GitService()
        self.ci_service = CIService(github_token)
        self.github_service = GitHubService(github_token) if github_token else None
        
        # Initialize database connection for repositories
        db = Neo4jConnection()
        self.ticket_repo = TicketRepository(db)
        self.message_repo = MessageRepository()  # Static methods, no db needed
        self.repository_repo = RepositoryRepository(db)
    
    async def process_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """
        Main entry point for ticket processing
        NOW USES LangGraph workflow for state machine orchestration
        
        Args:
            ticket_id: ID of the ticket to process
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Starting LangGraph ticket processing for {ticket_id}")
        
        # Execute the LangGraph workflow
        result = await self.workflow.execute(ticket_id)
        
        return result
    
    # Keep the legacy methods for backward compatibility and validation handling
    
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
