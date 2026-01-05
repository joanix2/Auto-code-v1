"""
Message Controller
API endpoints for managing messages in ticket conversations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from ..models.message import Message, MessageCreate, MessageUpdate
from ..repositories.message_repository import MessageRepository
from ..repositories.ticket_repository import TicketRepository
from ..database import db
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
) -> Message:
    """
    Create a new message in a ticket conversation
    
    Args:
        message_data: Message creation data
        current_user: Authenticated user
        
    Returns:
        Created message
    """
    logger.info(f"User {current_user.username} creating message for ticket {message_data.ticket_id}")
    
    # Verify ticket exists
    db.connect()
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get_ticket_by_id(message_data.ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {message_data.ticket_id} not found"
        )
    
    # Create message
    message = Message(
        id="",  # Will be generated in repository
        ticket_id=message_data.ticket_id,
        role=message_data.role,
        content=message_data.content,
        metadata=message_data.metadata,
        model=message_data.model,
        tokens_used=message_data.tokens_used,
        step=message_data.step
    )
    
    message_repo = MessageRepository()
    created_message = message_repo.create(message)
    
    logger.info(f"Created message {created_message.id} for ticket {message_data.ticket_id}")
    return created_message


@router.get("/ticket/{ticket_id}", response_model=List[Message])
async def get_ticket_messages(
    ticket_id: str,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user)
) -> List[Message]:
    """
    Get all messages for a ticket
    
    Args:
        ticket_id: Ticket ID
        limit: Optional limit on number of messages
        current_user: Authenticated user
        
    Returns:
        List of messages ordered by timestamp
    """
    logger.info(f"User {current_user.username} fetching messages for ticket {ticket_id}")
    
    # Verify ticket exists
    db.connect()
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    message_repo = MessageRepository()
    messages = message_repo.get_by_ticket_id(ticket_id, limit)
    
    logger.info(f"Retrieved {len(messages)} messages for ticket {ticket_id}")
    return messages


@router.get("/ticket/{ticket_id}/latest", response_model=Message)
async def get_latest_message(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
) -> Message:
    """
    Get the most recent message for a ticket
    
    Args:
        ticket_id: Ticket ID
        current_user: Authenticated user
        
    Returns:
        Latest message
    """
    logger.info(f"User {current_user.username} fetching latest message for ticket {ticket_id}")
    
    message_repo = MessageRepository()
    message = message_repo.get_latest_by_ticket_id(ticket_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No messages found for ticket {ticket_id}"
        )
    
    return message


@router.get("/ticket/{ticket_id}/step/{step}", response_model=List[Message])
async def get_messages_by_step(
    ticket_id: str,
    step: str,
    current_user: User = Depends(get_current_user)
) -> List[Message]:
    """
    Get messages for a specific workflow step
    
    Args:
        ticket_id: Ticket ID
        step: Workflow step (e.g., "analysis", "code_generation")
        current_user: Authenticated user
        
    Returns:
        List of messages for that step
    """
    logger.info(f"User {current_user.username} fetching {step} messages for ticket {ticket_id}")
    
    message_repo = MessageRepository()
    messages = message_repo.get_by_step(ticket_id, step)
    
    return messages


@router.get("/ticket/{ticket_id}/summary")
async def get_conversation_summary(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get summary statistics for a ticket's conversation
    
    Args:
        ticket_id: Ticket ID
        current_user: Authenticated user
        
    Returns:
        Conversation statistics
    """
    logger.info(f"User {current_user.username} fetching conversation summary for ticket {ticket_id}")
    
    # Verify ticket exists
    ticket_repo = TicketRepository()
    ticket = ticket_repo.get_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    message_repo = MessageRepository()
    summary = message_repo.get_conversation_summary(ticket_id)
    
    return summary


@router.get("/{message_id}", response_model=Message)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
) -> Message:
    """
    Get a specific message by ID
    
    Args:
        message_id: Message ID
        current_user: Authenticated user
        
    Returns:
        Message
    """
    message_repo = MessageRepository()
    message = message_repo.get_by_id(message_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found"
        )
    
    return message


@router.patch("/{message_id}", response_model=Message)
async def update_message(
    message_id: str,
    update_data: MessageUpdate,
    current_user: User = Depends(get_current_user)
) -> Message:
    """
    Update a message
    
    Args:
        message_id: Message ID
        update_data: Fields to update
        current_user: Authenticated user
        
    Returns:
        Updated message
    """
    logger.info(f"User {current_user.username} updating message {message_id}")
    
    message_repo = MessageRepository()
    updated_message = message_repo.update(
        message_id=message_id,
        content=update_data.content,
        metadata=update_data.metadata,
        tokens_used=update_data.tokens_used
    )
    
    if not updated_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found"
        )
    
    logger.info(f"Updated message {message_id}")
    return updated_message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a message
    
    Args:
        message_id: Message ID
        current_user: Authenticated user
    """
    logger.info(f"User {current_user.username} deleting message {message_id}")
    
    message_repo = MessageRepository()
    deleted = message_repo.delete(message_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message {message_id} not found"
        )
    
    logger.info(f"Deleted message {message_id}")


@router.delete("/ticket/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_messages(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete all messages for a ticket
    
    Args:
        ticket_id: Ticket ID
        current_user: Authenticated user
    """
    logger.info(f"User {current_user.username} deleting all messages for ticket {ticket_id}")
    
    # Verify ticket exists
    ticket_repo = TicketRepository()
    ticket = ticket_repo.get_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    message_repo = MessageRepository()
    deleted_count = message_repo.delete_by_ticket_id(ticket_id)
    
    logger.info(f"Deleted {deleted_count} messages for ticket {ticket_id}")
