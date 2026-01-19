"""
Message Controller - Manage PR comments and conversations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import logging
import uuid
import httpx

from ..base_controller import BaseController
from ...models.oauth.user import User
from ...models.repository.message import Message, MessageCreate
from ...services.repository.message_service import MessageService
from ...repositories.repository.message_repository import MessageRepository
from ...repositories.repository.issue_repository import IssueRepository
from ...repositories.repository.repository_repository import RepositoryRepository
from ...utils.auth import get_current_user
from ...database import get_db

router = APIRouter(prefix="/api/messages", tags=["messages"])
logger = logging.getLogger(__name__)


class MessageController(BaseController[Message, MessageCreate, None]):
    """Message Controller with CRUD operations and GitHub PR comment sync"""
    
    def __init__(
        self, 
        service: MessageService,
        issue_repository: IssueRepository,
        repository_repository: RepositoryRepository
    ):
        super().__init__(service)
        self.service = service
        self.issue_repository = issue_repository
        self.repository_repository = repository_repository
    
    def get_resource_name(self) -> str:
        return "message"
    
    def get_resource_name_plural(self) -> str:
        return "messages"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        return f"message-{uuid.uuid4()}"
    
    async def validate_create(self, data: MessageCreate, current_user: User, db) -> Dict[str, Any]:
        """
        Validate message creation and prepare data for GitHub sync
        
        Messages require parent issue context for GitHub PR comment creation
        """
        # Verify issue exists
        issue = await self.issue_repository.get_by_id(data.issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )
        
        # Verify issue has a PR (required for comments)
        if not issue.github_pr_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Issue does not have an associated pull request"
            )
        
        # Get repository info for GitHub API
        if not issue.repository_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Issue is not associated with a repository"
            )
        
        repository = await self.repository_repository.get_by_id(issue.repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        if not repository.full_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Repository full_name is missing"
            )
        
        # Prepare data with GitHub context
        return {
            "access_token": current_user.github_token,
            "content": data.content,
            "issue_id": data.issue_id,
            "author_username": current_user.username,
            "author_type": data.author_type or "user",
            "repository_full_name": repository.full_name,
            "pr_number": issue.github_pr_number
        }
    
    async def validate_update(self, resource_id: str, updates, current_user: User, db) -> Optional[Dict[str, Any]]:
        """Messages cannot be updated for now"""
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Messages cannot be updated"
        )
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Dict[str, Any]:
        """Validate message deletion and prepare data for GitHub sync"""
        message = await self.service.get_by_id(resource_id)
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
        
        # Get issue and repository info for GitHub API
        issue = await self.issue_repository.get_by_id(message.issue_id)
        if not issue or not issue.repository_id:
            logger.warning(f"Cannot sync message {resource_id} deletion to GitHub: issue or repository not found")
            # Return minimal data, will skip GitHub sync
            return {
                "access_token": current_user.github_token,
                "entity_id": resource_id
            }
        
        repository = await self.repository_repository.get_by_id(issue.repository_id)
        if not repository or not repository.full_name:
            logger.warning(f"Cannot sync message {resource_id} deletion to GitHub: repository full_name missing")
            return {
                "access_token": current_user.github_token,
                "entity_id": resource_id
            }
        
        return {
            "access_token": current_user.github_token,
            "entity_id": resource_id,
            "repository_full_name": repository.full_name
        }
    
    async def create(self, data: MessageCreate, current_user: User, db) -> Message:
        """Create message with GitHub PR comment sync"""
        try:
            validated_data = await self.validate_create(data, current_user, db)
            message = await self.service.create(validated_data)
            return message
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"GitHub API error: {e.response.text}"
            )
    
    async def delete(self, resource_id: str, current_user: User, db) -> Dict[str, str]:
        """Delete message with GitHub PR comment sync"""
        try:
            validated_data = await self.validate_delete(resource_id, current_user, db)
            await self.service.delete(resource_id, validated_data.get("access_token"), **validated_data)
            return {"message": f"Message {resource_id} deleted successfully"}
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"GitHub API error: {e.response.text}"
            )
    
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
        
        return await self.service.get_all({"issue_id": issue_id})


# Dependency to get controller instance
def get_message_controller(db = Depends(get_db)) -> MessageController:
    """FastAPI dependency to get MessageController instance"""
    message_repository = MessageRepository(db)
    issue_repository = IssueRepository(db)
    repository_repository = RepositoryRepository(db)
    message_service = MessageService(message_repository, issue_repository)
    return MessageController(message_service, issue_repository, repository_repository)


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

