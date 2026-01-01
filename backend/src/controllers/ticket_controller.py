"""Ticket controller - API endpoints for tickets"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from src.models.ticket import Ticket, TicketCreate, TicketUpdate
from src.models.user import User
from src.repositories.ticket_repository import TicketRepository
from src.database import Neo4jConnection
from src.utils.auth import get_current_user

router = APIRouter()


class TicketOrderUpdate(BaseModel):
    """Model for updating ticket order"""
    ticket_id: str
    order: int


class BulkOrderUpdate(BaseModel):
    """Model for bulk order updates"""
    updates: List[TicketOrderUpdate]


def get_ticket_repo():
    """Dependency to get ticket repository"""
    db = Neo4jConnection()
    return TicketRepository(db)


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

