"""
Message Service - Business logic for PR comments and conversations
"""
from typing import List, Optional, Dict, Any
import uuid
import logging
import httpx

from .base_service import GitHubSyncService
from ..repositories.message_repository import MessageRepository
from ..repositories.issue_repository import IssueRepository
from ..models.message import Message, MessageCreate

logger = logging.getLogger(__name__)


class MessageService(GitHubSyncService[Message]):
    """Service for message business logic with GitHub PR comments sync"""
    
    def __init__(self, message_repo: MessageRepository, issue_repo: IssueRepository = None):
        """
        Initialize message service
        
        Args:
            message_repo: Message repository instance
            issue_repo: Issue repository instance (optional, for fetching PR info)
        """
        self.message_repo = message_repo
        self.issue_repo = issue_repo
    
    # Implementation of GitHubSyncService helper methods
    
    async def _create_in_db(self, data: Dict[str, Any]) -> Message:
        """Create message in database"""
        return await self.message_repo.create(data)
    
    async def _update_in_db(self, entity_id: str, data: Dict[str, Any]) -> Optional[Message]:
        """Update message in database"""
        return await self.message_repo.update(entity_id, data)
    
    async def _delete_from_db(self, entity_id: str) -> bool:
        """Delete message from database"""
        return await self.message_repo.delete(entity_id)
    
    def _get_github_syncable_fields(self) -> List[str]:
        """Fields that should be synced with GitHub"""
        return ["content"]
    
    async def map_github_to_db(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map GitHub API response to database entity format"""
        return {
            "id": f"message-{github_data['id']}",
            "github_comment_id": github_data["id"],
            "github_comment_url": github_data["html_url"],
            "content": github_data["body"],
            "author_username": github_data["user"]["login"],
            "author_type": "user",  # GitHub comments are from users
        }
    
    # Implementation of BaseService interface
    
    async def get_by_id(self, entity_id: str) -> Optional[Message]:
        """Get message by ID"""
        return await self.message_repo.get_by_id(entity_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Message]:
        """Get all messages with optional filters"""
        if filters and "issue_id" in filters:
            return await self.message_repo.get_by_issue(filters["issue_id"])
        return await self.message_repo.get_all()
    
    # GitHub API methods (implementation of GitHubSyncService abstract methods)
    
    async def create_on_github(
        self,
        access_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create comment on GitHub PR/Issue
        
        Args:
            access_token: GitHub access token
            **kwargs: repository_full_name, pr_number (or issue_number), content
        """
        repository_full_name = kwargs.get("repository_full_name")
        pr_number = kwargs.get("pr_number") or kwargs.get("issue_number")
        content = kwargs.get("content")
        
        if not repository_full_name or not pr_number:
            raise ValueError("repository_full_name and pr_number are required")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{repository_full_name}/issues/{pr_number}/comments",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={"body": content}
            )
            response.raise_for_status()
            return response.json()
    
    async def update_on_github(
        self,
        access_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update comment on GitHub
        
        Args:
            access_token: GitHub access token
            **kwargs: entity_id, repository_full_name, content
        """
        # Get message to find comment ID
        entity_id = kwargs.get("entity_id")
        message = await self.message_repo.get_by_id(entity_id) if entity_id else None
        
        if not message or not message.github_comment_id:
            raise ValueError("Message not found or no GitHub comment ID")
        
        repository_full_name = kwargs.get("repository_full_name")
        if not repository_full_name:
            raise ValueError("repository_full_name is required")
        
        # Build update payload
        github_updates = {}
        if "content" in kwargs and kwargs["content"] is not None:
            github_updates["body"] = kwargs["content"]
        
        if not github_updates:
            return message.model_dump()
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://api.github.com/repos/{repository_full_name}/issues/comments/{message.github_comment_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json=github_updates
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_on_github(
        self,
        access_token: str,
        entity: Any,  # Message type
        **kwargs
    ) -> bool:
        """
        Delete comment on GitHub
        
        Args:
            access_token: GitHub access token
            entity: The message to delete
            **kwargs: repository_full_name
        """
        if not entity or not entity.github_comment_id:
            logger.warning(f"Cannot delete message on GitHub: no comment ID")
            return True  # Allow DB deletion anyway
        
        repository_full_name = kwargs.get("repository_full_name")
        if not repository_full_name:
            logger.warning(f"Cannot delete message on GitHub: no repository_full_name")
            return True
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://api.github.com/repos/{repository_full_name}/issues/comments/{entity.github_comment_id}",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                response.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            # If it's a 404, the comment is already gone
            if e.response and e.response.status_code == 404:
                return True
            raise
    
    # Implementation of SyncableService interface
    
    async def fetch_from_github_api(
        self,
        access_token: str,
        owner: str,
        repo_name: str,
        pr_number: int = None,
        issue_number: int = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch comments from GitHub API without creating DB records
        
        Args:
            access_token: GitHub access token
            owner: Repository owner
            repo_name: Repository name
            pr_number: PR number (or use issue_number)
            issue_number: Issue number (GitHub treats PR comments as issue comments)
            
        Returns:
            List of comment data from GitHub API
        """
        number = pr_number or issue_number
        if not number:
            raise ValueError("pr_number or issue_number is required")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/issues/{number}/comments",
                headers=headers
            )
            response.raise_for_status()
            github_comments = response.json()
        
        logger.debug(f"Fetched {len(github_comments)} comments from GitHub API")
        return github_comments
    
    async def sync_from_github(
        self,
        access_token: str,
        issue_id: str = None,
        owner: str = None,
        repo_name: str = None,
        pr_number: int = None,
        issue_number: int = None,
        **kwargs
    ) -> List[Message]:
        """
        Synchronize comments from GitHub PR/Issue to database
        
        Complex case: Need to get PR number from issue
        
        Args:
            access_token: GitHub access token
            issue_id: Issue ID in our database
            owner: Repository owner
            repo_name: Repository name
            pr_number: PR number (optional if issue_id provided)
            issue_number: Issue number
            
        Returns:
            List of synchronized messages
        """
        # If issue_id provided but no pr_number, fetch it from issue
        if issue_id and not pr_number and self.issue_repo:
            issue = await self.issue_repo.get_by_id(issue_id)
            if issue and issue.github_pr_number:
                pr_number = issue.github_pr_number
                logger.info(f"Resolved PR number {pr_number} from issue {issue_id}")
        
        if not owner or not repo_name:
            raise ValueError("owner and repo_name are required")
        
        number = pr_number or issue_number
        if not number:
            raise ValueError("pr_number or issue_number is required (or provide issue_id with issue_repo)")
        
        logger.info(f"Syncing comments for {owner}/{repo_name} PR/Issue #{number}")
        
        # Fetch from GitHub API
        github_comments = await self.fetch_from_github_api(
            access_token, 
            owner, 
            repo_name, 
            pr_number=number
        )
        
        synced_messages = []
        
        for gh_comment in github_comments:
            # Check if message already exists
            existing_message = await self.message_repo.get_by_github_comment_id(gh_comment["id"])
            
            # Map GitHub data to DB format
            message_data = await self.map_github_to_db(gh_comment)
            
            # Add issue_id if provided
            if issue_id:
                message_data["issue_id"] = issue_id
            
            if existing_message:
                # Update existing message
                message = await self.message_repo.update(existing_message.id, message_data)
                logger.debug(f"Updated comment {gh_comment['id']}")
            else:
                # Create new message
                message = await self.message_repo.create(message_data)
                logger.debug(f"Created comment {gh_comment['id']}")
            
            synced_messages.append(message)
        
        logger.info(f"Synced {len(synced_messages)} comments for PR/Issue #{number}")
        return synced_messages
    
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
        logger.info(f"Created message for issue {issue_id}")
        return message

