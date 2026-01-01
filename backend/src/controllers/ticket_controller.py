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
    ticket = await ticket_repo.create_ticket(ticket_data, current_user.username)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create ticket"
        )
    return ticket


@router.get("/tickets", response_model=List[Ticket])
async def get_tickets(
    repository: str,
    current_user: User = Depends(get_current_user),
    ticket_repo: TicketRepository = Depends(get_ticket_repo)
):
    """Get all tickets for a repository"""
    return await ticket_repo.get_tickets_by_repository(repository)
