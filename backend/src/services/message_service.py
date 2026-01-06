"""
Message Service - Business logic for PR comments and conversations
"""
from typing import List, Optional, Dict, Any
import uuid
import logging
import httpx

from .base_service import BaseService, SyncableService
from ..repositories.message_repository import MessageRepository
from ..models.message import Message, MessageCreate

logger = logging.getLogger(__name__)


class MessageService(BaseService[Message], SyncableService[Message]):
    """Service for message business logic with GitHub PR comments sync"""
    
    def __init__(self, message_repo: MessageRepository):
        """
        Initialize message service
        
        Args:
            message_repo: Message repository instance
        """
        self.message_repo = message_repo
    
    # Implementation of BaseService interface
    
    async def create(self, data: Dict[str, Any]) -> Message:
        """Create a new message in database"""
        return await self.message_repo.create(data)
    
    async def get_by_id(self, entity_id: str) -> Optional[Message]:
        """Get message by ID"""
        return await self.message_repo.get_by_id(entity_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Message]:
        """Get all messages with optional filters"""
        if filters and "issue_id" in filters:
            return await self.message_repo.get_by_issue(filters["issue_id"])
        return await self.message_repo.get_all()
    
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[Message]:
        """Update message"""
        return await self.message_repo.update(entity_id, update_data)
    
    async def delete(self, entity_id: str) -> bool:
        """Delete message"""
        return await self.message_repo.delete(entity_id)
    
    # Implementation of SyncableService interface
    
    async def fetch_from_github_api(
        self,
        access_token: str,
        owner: str,
        repo_name: str,
        issue_number: int,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch comments from GitHub API without creating DB records
        
        Args:
            access_token: GitHub access token
            owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number
            
        Returns:
            List of comment data from GitHub API
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/issues/{issue_number}/comments",
                headers=headers
            )
            response.raise_for_status()
            github_comments = response.json()
        
        logger.debug(f"Fetched {len(github_comments)} comments from GitHub API")
        return github_comments
    
    async def sync_from_github(
        self,
        access_token: str,
        issue_id: str,
        owner: str,
        repo_name: str,
        issue_number: int,
        **kwargs
    ) -> List[Message]:
        """
        Synchronize comments from GitHub API to database
        
        Args:
            access_token: GitHub access token
            issue_id: Issue ID in our database
            owner: Repository owner
            repo_name: Repository name
            issue_number: Issue number on GitHub
            
        Returns:
            List of synchronized messages
        """
        logger.info(f"Syncing comments for issue #{issue_number} in {owner}/{repo_name}")
        
        # Fetch from GitHub API first
        github_comments = await self.fetch_from_github_api(
            access_token, owner, repo_name, issue_number
        )
        
        synced_messages = []
        
        for gh_comment in github_comments:
            message_data = {
                "id": f"message-{gh_comment['id']}",
                "issue_id": issue_id,
                "content": gh_comment["body"],
                "author_username": gh_comment["user"]["login"],
                "author_type": "copilot" if "copilot" in gh_comment["user"]["login"].lower() else "user"
            }
            
            # Check if message already exists
            existing_message = await self.message_repo.get_by_id(message_data["id"])
            
            if not existing_message:
                message = await self.message_repo.create(message_data)
                synced_messages.append(message)
                logger.debug(f"Created message from comment {gh_comment['id']}")
        
        logger.info(f"Synced {len(synced_messages)} new messages")
        return synced_messages
    
    # Custom methods
    
    # Custom methods
    
    async def create_message(
        self,
        issue_id: str,
        content: str,
        author_username: str,
        author_type: str = "user"
    ) -> Message:
        """Convenience method to create a message"""
        message_data = {
            "id": f"message-{uuid.uuid4()}",
            "issue_id": issue_id,
            "content": content,
            "author_username": author_username,
            "author_type": author_type
        }
        
        message = await self.message_repo.create(message_data)
        logger.info(f"Created message {message.id} for issue {issue_id}")
        
        return message
    
    async def get_issue_messages(self, issue_id: str) -> List[Message]:
        """Get all messages for an issue"""
        return await self.message_repo.get_by_issue(issue_id)
    
    async def get_copilot_messages(self, issue_id: str) -> List[Message]:
        """Get all Copilot messages for an issue"""
        return await self.message_repo.get_copilot_messages(issue_id)

