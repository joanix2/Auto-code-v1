"""Ticket controller - API endpoints for tickets"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.models.ticket import Ticket, TicketCreate
from src.models.user import User
from src.repositories.ticket_repository import TicketRepository
from src.database import Neo4jConnection
from src.utils.auth import get_current_user

router = APIRouter()


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
