"""
Message Controller - Manage PR comments and conversations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
import uuid

from ..models.user import User
from ..models.message import Message, MessageCreate
from ..repositories.message_repository import MessageRepository
from ..repositories.issue_repository import IssueRepository
from ..utils.auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/messages", tags=["messages"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=Message)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new message (PR comment)
    
    Args:
        message_data: Message creation data
        
    Returns:
        Created message
    """
    message_repository = MessageRepository(db)
    issue_repository = IssueRepository(db)
    
    # Verify issue exists
    issue = await issue_repository.get_by_id(message_data.issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    # Create message
    data = message_data.dict()
    data["id"] = f"message-{uuid.uuid4()}"
    data["author_username"] = current_user.username
    
    message = await message_repository.create(data)
    logger.info(f"Created message {message.id} for issue {issue.id}")
    
    return message


@router.get("/issue/{issue_id}", response_model=List[Message])
async def list_messages_by_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List all messages for an issue
    
    Args:
        issue_id: Issue ID
        
    Returns:
        List of messages ordered by creation date
    """
    message_repository = MessageRepository(db)
    issue_repository = IssueRepository(db)
    
    # Verify issue exists
    issue = await issue_repository.get_by_id(issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    messages = await message_repository.get_by_issue(issue_id)
    return messages


@router.get("/{message_id}", response_model=Message)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get message by ID
    
    Args:
        message_id: Message ID
        
    Returns:
        Message details
    """
    message_repository = MessageRepository(db)
    message = await message_repository.get_by_id(message_id)
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message


@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete a message
    
    Args:
        message_id: Message ID
        
    Returns:
        Success message
    """
    message_repository = MessageRepository(db)
    
    message = await message_repository.get_by_id(message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check authorization (only author can delete)
    if message.author_username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this message"
        )
    
    deleted = await message_repository.delete(message_id)
    
    if deleted:
        return {"message": "Message deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )
