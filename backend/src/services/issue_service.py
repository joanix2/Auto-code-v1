"""
Issue Service - Business logic for issue management and GitHub sync
"""
from typing import List, Optional, Dict, Any
import logging
import httpx

from .base_service import BaseService, SyncableService
from ..repositories.issue_repository import IssueRepository
from ..models.issue import Issue, IssueCreate

logger = logging.getLogger(__name__)


class IssueService(BaseService[Issue], SyncableService[Issue]):
    """Service for issue business logic and GitHub synchronization"""
    
    def __init__(self, issue_repo: IssueRepository):
        """
        Initialize issue service
        
        Args:
            issue_repo: Issue repository instance
        """
        self.issue_repo = issue_repo
    
    # Implementation of BaseService interface
    
    async def create(self, data: Dict[str, Any]) -> Issue:
        """Create a new issue in database"""
        return await self.issue_repo.create(data)
    
    async def get_by_id(self, entity_id: str) -> Optional[Issue]:
        """Get issue by ID"""
        return await self.issue_repo.get_by_id(entity_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """Get all issues with optional filters"""
        if filters and "repository_id" in filters:
            status = filters.get("status")
            return await self.issue_repo.get_by_repository(filters["repository_id"], status)
        return await self.issue_repo.get_all()
    
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[Issue]:
        """Update issue"""
        return await self.issue_repo.update(entity_id, update_data)
    
    async def delete(self, entity_id: str) -> bool:
        """Delete issue"""
        return await self.issue_repo.delete(entity_id)
    
    # Implementation of SyncableService interface
    
    async def fetch_from_github_api(
        self,
        access_token: str,
        owner: str,
        repo_name: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch issues from GitHub API without creating DB records
        
        Args:
            access_token: GitHub access token
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            List of issue data from GitHub API
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/issues",
                headers=headers,
                params={"state": "all", "per_page": 100}
            )
            response.raise_for_status()
            github_issues = response.json()
        
        # Filter out pull requests (they appear in issues API)
        issues_only = [issue for issue in github_issues if "pull_request" not in issue]
        
        logger.debug(f"Fetched {len(issues_only)} issues from GitHub API")
        return issues_only
    
    async def sync_from_github(
        self,
        access_token: str,
        repository_id: str,
        owner: str,
        repo_name: str,
        **kwargs
    ) -> List[Issue]:
        """
        Synchronize issues from GitHub API to database
        
        Args:
            access_token: GitHub access token
            repository_id: Repository ID in our database
            owner: Repository owner
            repo_name: Repository name
            
        Returns:
            List of synchronized issues
        """
        logger.info(f"Syncing issues for {owner}/{repo_name}")
        
        # Fetch from GitHub API first
        github_issues = await self.fetch_from_github_api(access_token, owner, repo_name)
        
        synced_issues = []
        
        for gh_issue in github_issues:
            # Check if issue already exists
            existing_issue = await self.issue_repo.get_by_github_id(gh_issue["id"])
            
            issue_data = {
                "repository_id": repository_id,
                "github_id": gh_issue["id"],
                "number": gh_issue["number"],
                "title": gh_issue["title"],
                "description": gh_issue.get("body", ""),
                "status": gh_issue["state"],  # open, closed
                "html_url": gh_issue["html_url"],
                "labels": [label["name"] for label in gh_issue.get("labels", [])]
            }
            
            if existing_issue:
                # Update existing issue
                issue = await self.issue_repo.update(existing_issue.id, issue_data)
                logger.debug(f"Updated issue #{gh_issue['number']}")
            else:
                # Create new issue
                issue_data["id"] = f"issue-{gh_issue['id']}"
                issue = await self.issue_repo.create(issue_data)
                logger.debug(f"Created issue #{gh_issue['number']}")
            
            synced_issues.append(issue)
        
        logger.info(f"Synced {len(synced_issues)} issues for {owner}/{repo_name}")
        return synced_issues
    
    # Custom methods
    
    # Custom methods
    
    async def get_by_repository(
        self,
        repository_id: str,
        status: Optional[str] = None
    ) -> List[Issue]:
        """Get all issues for a repository"""
        return await self.issue_repo.get_by_repository(repository_id, status)
    
    async def get_by_github_id(self, github_id: int) -> Optional[Issue]:
        """Get issue by GitHub ID"""
        return await self.issue_repo.get_by_github_id(github_id)
    
    async def assign_to_copilot(
        self,
        issue_id: str,
        assigned_to_copilot: bool = True
    ) -> Optional[Issue]:
        """Assign/unassign issue to GitHub Copilot"""
        issue = await self.issue_repo.assign_to_copilot(issue_id, assigned_to_copilot)
        
        if issue:
            action = "Assigned" if assigned_to_copilot else "Unassigned"
            logger.info(f"{action} issue {issue_id} to Copilot")
        
        return issue
    
    async def get_copilot_issues(self, repository_id: str) -> List[Issue]:
        """Get all issues assigned to Copilot for a repository"""
        return await self.issue_repo.get_copilot_issues(repository_id)

