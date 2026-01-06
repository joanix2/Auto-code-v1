"""
Agent Controller
API endpoints for SimpleClaudeAgent
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from pathlib import Path

from ..agent.simple_claude_agent import SimpleClaudeAgent
from ..repositories.ticket_repository import TicketRepository
from ..repositories.repository_repository import RepositoryRepository
from ..models.ticket import Ticket
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


class AgentDevelopRequest(BaseModel):
    """Request to develop a ticket with SimpleClaudeAgent"""
    ticket_id: str


class AgentDevelopResponse(BaseModel):
    """Response from agent development"""
    success: bool
    ticket_id: str
    status: str
    iterations: int
    message: str
    details: Optional[Dict[str, Any]] = None


@router.post("/develop-ticket", response_model=AgentDevelopResponse)
async def develop_ticket_with_agent(
    request: AgentDevelopRequest,
    current_user: User = Depends(get_current_user)
) -> AgentDevelopResponse:
    """
    Develop a ticket using SimpleClaudeAgent (Claude Opus 4)
    
    This endpoint triggers autonomous development workflow:
    1. Analyze ticket requirements
    2. Generate implementation code
    3. Apply file modifications
    4. Validate changes
    
    Args:
        request: Development request with ticket ID
        current_user: Authenticated user
        
    Returns:
        AgentDevelopResponse with processing results
    """
    logger.info(f"User {current_user.username} requested agent development for ticket {request.ticket_id}")
    
    try:
        # Get ticket from database
        ticket_repo = TicketRepository()
        ticket = ticket_repo.get_by_id(request.ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {request.ticket_id} not found"
            )
        
        # Get repository information
        repo_repo = RepositoryRepository()
        repository = repo_repo.get_repository_by_id(ticket.repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {ticket.repository_id} not found"
            )
        
        # Initialize SimpleClaudeAgent
        agent = SimpleClaudeAgent()
        
        # Process ticket with agent
        repository_path = Path(repository.local_path)
        result = agent.process_ticket(
            ticket=ticket,
            repository_path=repository_path
        )
        
        # Update ticket status based on result
        if result["success"]:
            ticket.status = "PENDING_VALIDATION"
            ticket_repo.update(ticket)
            logger.info(f"Agent successfully developed ticket {request.ticket_id}")
        else:
            logger.warning(f"Agent failed to develop ticket {request.ticket_id}")
        
        return AgentDevelopResponse(
            success=result["success"],
            ticket_id=request.ticket_id,
            status="completed" if result["success"] else "failed",
            iterations=1,  # SimpleClaudeAgent doesn't use iterations like LangGraph
            message=result.get("message", "Agent processing completed"),
            details=result.get("details", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in agent development: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent development failed: {str(e)}"
        )


@router.get("/status/{ticket_id}")
async def get_agent_status(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get the status of agent development for a ticket
    
    Args:
        ticket_id: Ticket ID to check
        current_user: Authenticated user
        
    Returns:
        Status information
    """
    # This would need to be implemented with a state store
    # For now, return basic info
    return {
        "ticket_id": ticket_id,
        "message": "Agent status tracking not yet implemented",
        "note": "Check ticket status for completion"
    }
