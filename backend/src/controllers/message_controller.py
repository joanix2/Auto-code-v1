"""
Message Controller - Manage PR comments and conversations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging
import uuid

from .base_controller import BaseController
from ..models.user import User
from ..models.message import Message, MessageCreate
from ..repositories.message_repository import MessageRepository
from ..repositories.issue_repository import IssueRepository
from ..utils.auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/messages", tags=["messages"])
logger = logging.getLogger(__name__)


class MessageController(BaseController[Message, MessageCreate, None]):
    """Message Controller with CRUD operations"""
    
    def __init__(self, repository: MessageRepository, issue_repository: IssueRepository):
        super().__init__(repository)
        self.issue_repository = issue_repository
    
    def get_resource_name(self) -> str:
        return "message"
    
    def get_resource_name_plural(self) -> str:
        return "messages"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        return f"message-{uuid.uuid4()}"
    
    async def validate_create(self, data: MessageCreate, current_user: User, db) -> Dict[str, Any]:
        # Verify issue exists
        issue = await self.issue_repository.get_by_id(data.issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )
        
        # Prepare data
        validated_data = data.dict()
        validated_data["author_username"] = current_user.username
        return validated_data
    
    async def validate_update(self, resource_id: str, updates, current_user: User, db) -> None:
        # Messages cannot be updated
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Messages cannot be updated"
        )
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Message:
        message = await self.repository.get_by_id(resource_id)
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
        
        return message
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Message]:
        # Messages are not synced from GitHub (they're PR comments)
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Messages cannot be synced from GitHub"
        )
    
    async def get_by_issue(self, issue_id: str) -> List[Message]:
        """Get all messages for an issue"""
        # Verify issue exists
        issue = await self.issue_repository.get_by_id(issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )
        
        return await self.repository.get_by_issue(issue_id)


# Dependency to get controller instance
def get_message_controller(db = Depends(get_db)) -> MessageController:
    """FastAPI dependency to get MessageController instance"""
    message_repository = MessageRepository(db)
    issue_repository = IssueRepository(db)
    return MessageController(message_repository, issue_repository)


# Route handlers

@router.post("/", response_model=Message)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MessageController = Depends(get_message_controller)
):
    """Create a new message (PR comment)"""
    return await controller.create(message_data, current_user, db)


@router.get("/issue/{issue_id}", response_model=List[Message])
async def list_messages_by_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    controller: MessageController = Depends(get_message_controller)
):
    """List all messages for an issue"""
    return await controller.get_by_issue(issue_id)


@router.get("/{message_id}", response_model=Message)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MessageController = Depends(get_message_controller)
):
    """Get message by ID"""
    return await controller.get_by_id(message_id, current_user, db)


@router.delete("/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MessageController = Depends(get_message_controller)
):
    """Delete a message"""
    return await controller.delete(message_id, current_user, db)

