"""
Repository Service - Business logic for repository management and GitHub sync
"""
from typing import List, Optional, Dict, Any
import logging
import httpx

from .base_service import BaseService, SyncableService
from ..repositories.repository_repository import RepositoryRepository
from ..models.repository import Repository, RepositoryCreate

logger = logging.getLogger(__name__)


class RepositoryService(BaseService[Repository], SyncableService[Repository]):
    """Service for repository business logic and GitHub synchronization"""
    
    def __init__(self, repo_repository: RepositoryRepository):
        """
        Initialize repository service
        
        Args:
            repo_repository: Repository repository instance
        """
        self.repo_repository = repo_repository
    
    # Implementation of BaseService interface
    
    async def create(self, data: Dict[str, Any]) -> Repository:
        """Create a new repository in database"""
        return await self.repo_repository.create(data)
    
    async def get_by_id(self, entity_id: str) -> Optional[Repository]:
        """Get repository by ID"""
        return await self.repo_repository.get_by_id(entity_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Repository]:
        """Get all repositories with optional filters"""
        if filters and "owner" in filters:
            return await self.repo_repository.get_by_owner(filters["owner"])
        return await self.repo_repository.get_all()
    
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[Repository]:
        """Update repository"""
        return await self.repo_repository.update(entity_id, update_data)
    
    async def delete(self, entity_id: str) -> bool:
        """Delete repository"""
        return await self.repo_repository.delete(entity_id)
    
    # Implementation of SyncableService interface
    
    async def fetch_from_github_api(
        self,
        access_token: str,
        username: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch repositories from GitHub API without creating DB records
        
        Args:
            access_token: GitHub access token
            username: GitHub username (if not provided, fetches authenticated user's repos)
            
        Returns:
            List of repository data from GitHub API
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Determine which endpoint to use
        if username:
            url = f"https://api.github.com/users/{username}/repos"
        else:
            url = "https://api.github.com/user/repos"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params={"per_page": 100, "sort": "updated"}
            )
            response.raise_for_status()
            github_repos = response.json()
        
        logger.debug(f"Fetched {len(github_repos)} repositories from GitHub API")
        return github_repos
    
    async def sync_from_github(
        self,
        access_token: str,
        username: Optional[str] = None,
        **kwargs
    ) -> List[Repository]:
        """
        Synchronize repositories from GitHub API to database
        
        Args:
            access_token: GitHub access token
            username: GitHub username
            
        Returns:
            List of synchronized repositories
        """
        logger.info(f"Syncing repositories for user {username or 'authenticated user'}")
        
        # Fetch from GitHub API first
        github_repos = await self.fetch_from_github_api(access_token, username)
        
        synced_repos = []
        
        for gh_repo in github_repos:
            # Check if repository already exists
            existing_repo = await self.repo_repository.get_by_github_id(gh_repo["id"])
            
            repo_data = {
                "github_id": gh_repo["id"],
                "owner_username": gh_repo["owner"]["login"],
                "name": gh_repo["name"],
                "full_name": gh_repo["full_name"],
                "description": gh_repo.get("description"),
                "is_private": gh_repo["private"],
                "default_branch": gh_repo["default_branch"],
            }
            
            if existing_repo:
                # Update existing repository
                repo = await self.repo_repository.update(existing_repo.id, repo_data)
                logger.debug(f"Updated repository {repo.full_name}")
            else:
                # Create new repository
                repo_data["id"] = f"repo-{gh_repo['id']}"
                repo = await self.repo_repository.create(repo_data)
                logger.debug(f"Created repository {repo.full_name}")
            
            synced_repos.append(repo)
        
        logger.info(f"Synced {len(synced_repos)} repositories")
        return synced_repos
    
    # Custom methods
    
    # Custom methods
    
    async def get_by_full_name(self, full_name: str) -> Optional[Repository]:
        """Get repository by full name (owner/repo)"""
        return await self.repo_repository.get_by_full_name(full_name)
    
    async def get_by_owner(self, owner: str) -> List[Repository]:
        """Get all repositories for a user/organization"""
        return await self.repo_repository.get_by_owner(owner)
    
    async def get_by_github_id(self, github_id: int) -> Optional[Repository]:
        """Get repository by GitHub ID"""
        return await self.repo_repository.get_by_github_id(github_id)

