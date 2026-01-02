"""
Ticket Processing Controller
API endpoints for triggering and managing ticket processing workflow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from ..services.ticket_processing_service import TicketProcessingService
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tickets/processing", tags=["ticket-processing"])


class ProcessTicketRequest(BaseModel):
    """Request to process a ticket"""
    ticket_id: str


class ValidationResultRequest(BaseModel):
    """Human validation result"""
    ticket_id: str
    approved: bool
    feedback: Optional[str] = None


@router.post("/start")
async def start_ticket_processing(
    request: ProcessTicketRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Start automated processing for a ticket
    
    This triggers the complete workflow:
    1. Prepare repository (clone/pull, branch management)
    2. LLM reasoning and code generation
    3. CI/CD execution
    4. Validation workflow
    
    Args:
        request: Processing request with ticket ID
        current_user: Authenticated user
        
    Returns:
        Processing result
    """
    logger.info(f"User {current_user.username} starting processing for ticket {request.ticket_id}")
    
    try:
        # Get GitHub token from user (if available)
        github_token = getattr(current_user, 'github_token', None)
        
        # Initialize processing service
        service = TicketProcessingService(github_token=github_token)
        
        # Start processing
        result = await service.process_ticket(request.ticket_id)
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error processing ticket: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.post("/validation")
async def submit_validation_result(
    request: ValidationResultRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Submit human validation result for a ticket
    
    After automated processing completes, a human reviews the changes
    and approves or rejects them. This endpoint handles that feedback.
    
    Args:
        request: Validation result with approval status and optional feedback
        current_user: Authenticated user
        
    Returns:
        Result of validation handling
    """
    logger.info(f"User {current_user.username} submitting validation for ticket {request.ticket_id}")
    
    try:
        # Get GitHub token
        github_token = getattr(current_user, 'github_token', None)
        
        # Initialize service
        service = TicketProcessingService(github_token=github_token)
        
        # Handle validation
        result = await service.handle_validation_result(
            ticket_id=request.ticket_id,
            approved=request.approved,
            feedback=request.feedback
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error handling validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation handling failed: {str(e)}"
        )


@router.get("/status/{ticket_id}")
async def get_processing_status(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current processing status for a ticket
    
    Args:
        ticket_id: Ticket ID
        current_user: Authenticated user
        
    Returns:
        Current processing status
    """
    from ..repositories.ticket_repository import TicketRepository
    from ..repositories.message_repository import MessageRepository
    
    ticket_repo = TicketRepository()
    message_repo = MessageRepository()
    
    # Get ticket
    ticket = ticket_repo.get_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    # Get conversation summary
    conversation_summary = message_repo.get_conversation_summary(ticket_id)
    
    return {
        "ticket_id": ticket_id,
        "status": ticket.status,
        "iteration_count": ticket.iteration_count,
        "conversation": conversation_summary
    }
