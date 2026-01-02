"""Ticket controller - API endpoints for tickets"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from src.models.ticket import Ticket, TicketCreate, TicketUpdate, TicketStatus
from src.models.user import User
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository
from src.services.claude_service import ClaudeService
from src.services.opencode_service import OpenCodeService
from src.database import Neo4jConnection
from src.utils.auth import get_current_user
import os

router = APIRouter()


class TicketOrderUpdate(BaseModel):
    """Model for updating ticket order"""
    ticket_id: str
    order: int


class BulkOrderUpdate(BaseModel):
    """Model for bulk order updates"""
    updates: List[TicketOrderUpdate]


class ClaudeDevelopRequest(BaseModel):
    """Model for Claude development request"""
    ticket_id: Optional[str] = None
    additional_context: Optional[str] = None
    auto_update_status: bool = True


class NextTicketResponse(BaseModel):
    """Model for next ticket in queue response"""
    ticket: Optional[Ticket] = None
    queue_position: int = 0
    total_open_tickets: int = 0


def get_ticket_repo():
    """Dependency to get ticket repository"""
    db = Neo4jConnection()
    return TicketRepository(db)


def get_repository_repo():
    """Dependency to get repository repository"""
    db = Neo4jConnection()
    return RepositoryRepository(db)


@router.post("/tickets", response_model=Ticket, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Create a new ticket"""
    try:
        ticket = await ticket_repo.create_ticket(ticket_data, current_user.username)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create ticket - repository not found or invalid data"
            )
        return ticket
    except Exception as e:
        print(f"Error creating ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating ticket: {str(e)}"
        )


@router.get("/tickets", response_model=List[Ticket])
async def get_tickets(
    repository: str,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Get all tickets for a repository"""
    return await ticket_repo.get_tickets_by_repository(repository)


@router.get("/tickets/repository/{repository_id}", response_model=List[Ticket])
async def get_tickets_by_repository(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Get all tickets for a specific repository by ID"""
    return await ticket_repo.get_tickets_by_repository(repository_id)


@router.put("/tickets/reorder", status_code=status.HTTP_200_OK)
async def reorder_tickets(
    bulk_update: BulkOrderUpdate,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Reorder multiple tickets at once"""
    try:
        for update in bulk_update.updates:
            ticket_data = TicketUpdate(order=update.order)
            await ticket_repo.update_ticket(update.ticket_id, ticket_data)
        return {"message": "Tickets reordered successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reordering tickets: {str(e)}"
        )


@router.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Get a specific ticket by ID"""
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.put("/tickets/{ticket_id}", response_model=Ticket)
async def update_ticket(
    ticket_id: str,
    ticket_data: TicketUpdate,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Update a ticket"""
    ticket = await ticket_repo.update_ticket(ticket_id, ticket_data)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return ticket


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Delete a ticket"""
    success = await ticket_repo.delete_ticket(ticket_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return None


@router.get("/tickets/repository/{repository_id}/next", response_model=NextTicketResponse)
async def get_next_ticket_in_queue(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """
    Get the next ticket to work on (first open ticket in order)
    """
    # Get all open tickets for the repository
    all_tickets = await ticket_repo.get_tickets_by_repository(repository_id)
    open_tickets = [t for t in all_tickets if t.status == TicketStatus.open]
    
    # Sort by order (already sorted from DB, but just to be sure)
    open_tickets.sort(key=lambda t: t.order)
    
    next_ticket = open_tickets[0] if open_tickets else None
    
    return NextTicketResponse(
        ticket=next_ticket,
        queue_position=1 if next_ticket else 0,
        total_open_tickets=len(open_tickets)
    )


@router.post("/tickets/{ticket_id}/develop-with-claude")
async def develop_ticket_with_claude(
    ticket_id: str,
    request: Optional[ClaudeDevelopRequest] = None,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """
    Use Claude AI to develop a ticket implementation
    
    This endpoint:
    1. Fetches the ticket details
    2. Generates a structured prompt
    3. Calls Claude API to get implementation
    4. Optionally updates ticket status to in_progress
    
    Requires ANTHROPIC_API_KEY environment variable
    """
    # Check if API key is configured
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Claude API key not configured. Set ANTHROPIC_API_KEY environment variable."
        )
    
    # Get ticket
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Get repository
    repository = await repo_repo.get_repository_by_id(ticket.repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    try:
        # Initialize Claude service
        claude_service = ClaudeService()
        
        # Develop ticket
        result = await claude_service.develop_ticket(
            ticket_title=ticket.title,
            ticket_description=ticket.description,
            ticket_type=ticket.ticket_type,
            priority=ticket.priority,
            repository_name=repository.name,
            repository_path=repository.url,
            additional_context=request.additional_context if request else None
        )
        
        # Update ticket status if requested
        if request and request.auto_update_status:
            update_data = TicketUpdate(status=TicketStatus.pending_validation)
            await ticket_repo.update_ticket(ticket_id, update_data)
        
        return {
            "ticket_id": ticket_id,
            "ticket_title": ticket.title,
            "repository": repository.name,
            "claude_response": result["content"],
            "usage": result.get("usage"),
            "model": result.get("model"),
            "status_updated": request.auto_update_status if request else True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling Claude API: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/develop-with-opencode")
async def develop_ticket_with_opencode(
    ticket_id: str,
    request: ClaudeDevelopRequest,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """
    Use OpenCode AI in Docker container to develop a ticket
    
    This endpoint:
    1. Starts the OpenCode container if needed
    2. Clones/updates the repository
    3. Runs OpenCode to implement the ticket
    4. Returns the results
    5. Optionally updates ticket status to pending_validation
    """
    # Get ticket
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Get repository
    repository = await repo_repo.get_repository_by_id(ticket.repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Get user for GitHub token
    from src.repositories.user_repository import UserRepository
    user = UserRepository.get_by_username(current_user.username)
    
    if not user or not user.github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub token not configured. Please configure it in your profile."
        )
    
    try:
        # Initialize OpenCode service
        opencode_service = OpenCodeService()
        
        # Develop ticket with OpenCode
        result = await opencode_service.develop_ticket(
            ticket_title=ticket.title,
            ticket_description=ticket.description,
            ticket_type=ticket.ticket_type,
            priority=ticket.priority,
            repository_url=repository.url,
            github_token=user.github_token,
            additional_context=request.additional_context
        )
        
        # Update ticket status if successful and requested
        if result["success"] and request.auto_update_status:
            await ticket_repo.update_ticket_status(
                ticket_id,
                TicketStatus.pending_validation
            )
        
        return {
            "success": result["success"],
            "ticket_id": ticket_id,
            "repository": repository.name,
            "output": result["output"],
            "errors": result["errors"],
            "repository_path": result["repository_path"],
            "status_updated": result["success"] and request.auto_update_status
        }
        
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OpenCode service not properly configured: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calling OpenCode: {str(e)}"
        )


@router.post("/tickets/repository/{repository_id}/develop-next")
async def develop_next_ticket_in_queue(
    repository_id: str,
    additional_context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """
    Automatically develop the next ticket in the queue
    
    This is a convenience endpoint that:
    1. Finds the next open ticket
    2. Calls Claude to implement it
    3. Updates the ticket status to in_progress
    """
    # Get next ticket
    all_tickets = await ticket_repo.get_tickets_by_repository(repository_id)
    open_tickets = [t for t in all_tickets if t.status == TicketStatus.open]
    open_tickets.sort(key=lambda t: t.order)
    
    if not open_tickets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No open tickets in queue"
        )
    
    next_ticket = open_tickets[0]
    
    # Develop with Claude
    request = ClaudeDevelopRequest(
        ticket_id=next_ticket.id,
        additional_context=additional_context,
        auto_update_status=True
    )
    
    return await develop_ticket_with_claude(
        ticket_id=next_ticket.id,
        request=request,
        current_user=current_user,
        ticket_repo=ticket_repo,
        repo_repo=repo_repo
    )
