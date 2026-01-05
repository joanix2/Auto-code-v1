"""
Ticket Processing Controller
API endpoints for triggering and managing ticket processing workflow
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from ..services import TicketProcessingService
from ..utils.auth import get_current_user
from ..models.user import User
from ..repositories.ticket_repository import TicketRepository
from ..database import Neo4jConnection
from ..websocket.connection_manager import manager

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


def get_ticket_repo():
    """Dependency to get ticket repository"""
    db = Neo4jConnection()
    return TicketRepository(db)


@router.post("/start")
async def start_ticket_processing(
    request: ProcessTicketRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
) -> Dict[str, Any]:
    """
    Start automated processing for a ticket (ASYNCHRONOUS)
    
    This endpoint:
    1. Immediately sets ticket status to PENDING
    2. Returns success response to client
    3. Launches background task for the complete workflow
    4. Sends real-time updates via WebSocket
    
    The client should connect to WebSocket endpoint:
    ws://localhost:8000/ws/tickets/{ticket_id}
    
    Args:
        request: Processing request with ticket ID
        background_tasks: FastAPI background tasks
        current_user: Authenticated user
        
    Returns:
        Immediate response with ticket status PENDING
    """
    logger.info(f"User {current_user.username} starting processing for ticket {request.ticket_id}")
    
    try:
        # Verify ticket exists
        ticket = await ticket_repo.get_ticket_by_id(request.ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {request.ticket_id} not found"
            )
        
        # Set ticket status to IN_PROGRESS immediately
        from ..models.ticket import TicketUpdate, TicketStatus
        update_data = TicketUpdate(status=TicketStatus.in_progress)
        await ticket_repo.update_ticket(request.ticket_id, update_data)
        
        # Send WebSocket update
        await manager.send_status_update(
            request.ticket_id,
            "IN_PROGRESS",
            "Traitement automatique en cours de démarrage...",
            progress=0
        )
        
        # Get GitHub token from user (if available)
        github_token = getattr(current_user, 'github_token', None)
        
        # Launch background task
        background_tasks.add_task(
            _process_ticket_background,
            request.ticket_id,
            github_token
        )
        
        return {
            "success": True,
            "ticket_id": request.ticket_id,
            "status": "IN_PROGRESS",
            "message": "Traitement automatique lancé en arrière-plan. Connectez-vous au WebSocket pour les mises à jour en temps réel.",
            "websocket_url": f"/ws/tickets/{request.ticket_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting ticket processing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start processing: {str(e)}"
        )


async def _process_ticket_background(ticket_id: str, github_token: Optional[str] = None):
    """
    Background task for processing a ticket
    
    Args:
        ticket_id: Ticket ID to process
        github_token: Optional GitHub token
    """
    try:
        logger.info(f"Background processing started for ticket {ticket_id}")
        
        # Initialize processing service
        service = TicketProcessingService(github_token=github_token)
        
        # Process ticket (this will send WebSocket updates)
        result = await service.process_ticket(ticket_id)
        
        # Send final update
        if result.get("success"):
            await manager.send_status_update(
                ticket_id,
                "COMPLETED",
                "Traitement automatique terminé avec succès",
                progress=100,
                data=result
            )
        else:
            await manager.send_status_update(
                ticket_id,
                "FAILED",
                "Traitement automatique échoué",
                error=result.get("error", "Unknown error"),
                data=result
            )
        
        logger.info(f"Background processing completed for ticket {ticket_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for ticket {ticket_id}: {e}", exc_info=True)
        await manager.send_status_update(
            ticket_id,
            "FAILED",
            "Erreur lors du traitement automatique",
            error=str(e)
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
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
) -> Dict[str, Any]:
    """
    Get current processing status for a ticket
    
    Args:
        ticket_id: Ticket ID
        current_user: Authenticated user
        
    Returns:
        Current processing status
    """
    from ..repositories.message_repository import MessageRepository
    
    db = Neo4jConnection()
    message_repo = MessageRepository(db)
    
    # Get ticket
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    # Get conversation summary
    conversation_summary = await message_repo.get_conversation_summary(ticket_id)
    
    return {
        "ticket_id": ticket_id,
        "status": ticket.status,
        "iteration_count": ticket.iteration_count,
        "conversation": conversation_summary
    }
