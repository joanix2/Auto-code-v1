"""
Issue Service - Business logic for issue management and GitHub sync
"""
from typing import List, Optional, Dict, Any
import logging
import httpx

from .base_service import GitHubSyncService
from ..repositories.issue_repository import IssueRepository
from ..repositories.repository_repository import RepositoryRepository
from ..models.issue import Issue, IssueCreate

logger = logging.getLogger(__name__)


class IssueService(GitHubSyncService[Issue]):
    """Service for issue business logic and GitHub synchronization"""
    
    def __init__(self, issue_repo: IssueRepository, repo_repository: Optional[RepositoryRepository] = None):
        """
        Initialize issue service
        
        Args:
            issue_repo: Issue repository instance
            repo_repository: Repository repository instance (optional, needed for updates)
        """
        self.issue_repo = issue_repo
        self.repo_repository = repo_repository
    
    # Implementation of GitHubSyncService helper methods
    
    async def _create_in_db(self, data: Dict[str, Any]) -> Issue:
        """Create issue in database"""
        return await self.issue_repo.create(data)
    
    async def _update_in_db(self, entity_id: str, data: Dict[str, Any]) -> Optional[Issue]:
        """Update issue in database"""
        return await self.issue_repo.update(entity_id, data)
    
    async def _delete_from_db(self, entity_id: str) -> bool:
        """Delete issue from database"""
        return await self.issue_repo.delete(entity_id)
    
    def _get_github_syncable_fields(self) -> List[str]:
        """Fields that should be synced with GitHub"""
        return ["title", "description", "status", "labels"]
    
    async def map_github_to_db(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map GitHub API response to database entity format"""
        # Extract data that might have been passed along
        db_data = {
            "id": f"issue-{github_data['id']}",
            "github_id": github_data["id"],
            "github_issue_number": github_data["number"],
            "title": github_data["title"],
            "description": github_data.get("body", ""),
            "status": "open" if github_data["state"] == "open" else "closed",
            "github_issue_url": github_data["html_url"],
            "labels": [label["name"] for label in github_data.get("labels", [])]
        }
        
        # Get author from GitHub user data
        if "user" in github_data and github_data["user"]:
            db_data["author_username"] = github_data["user"].get("login", "")
        
        # These fields come from the original request data, not from GitHub
        # They should be passed through the context
        if "_context" in github_data:
            context = github_data["_context"]
            if "repository_id" in context:
                db_data["repository_id"] = context["repository_id"]
            if "author_username" in context:
                db_data["author_username"] = context["author_username"]
            if "priority" in context:
                db_data["priority"] = context["priority"]
            if "issue_type" in context:
                db_data["issue_type"] = context["issue_type"]
        
        # Set defaults for fields not in GitHub
        if "priority" not in db_data:
            db_data["priority"] = "medium"
        if "issue_type" not in db_data:
            db_data["issue_type"] = "feature"
        
        return db_data
    
    # Implementation of BaseService interface
    
    async def create(self, data: Dict[str, Any]) -> Issue:
        """
        Create issue on GitHub AND in database (orchestration)
        
        Overrides base create to pass context through to map_github_to_db
        """
        access_token = data.pop("access_token")
        
        # Save context that GitHub won't return
        context = {
            "repository_id": data.get("repository_id"),
            "author_username": data.get("author_username"),
            "priority": data.get("priority", "medium"),
            "issue_type": data.get("issue_type", "feature")
        }
        
        # 1. Create on GitHub first
        github_response = await self.create_on_github(access_token=access_token, **data)
        
        # 2. Add context to GitHub response
        github_response["_context"] = context
        
        # 3. Map GitHub response to DB format
        db_data = await self.map_github_to_db(github_response)
        
        # 4. Create in database
        return await self._create_in_db(db_data)
    
    async def get_by_id(self, entity_id: str) -> Optional[Issue]:
        """Get issue by ID"""
        return await self.issue_repo.get_by_id(entity_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Issue]:
        """Get all issues with optional filters"""
        if filters and "repository_id" in filters:
            status = filters.get("status")
            return await self.issue_repo.get_by_repository(filters["repository_id"], status)
        return await self.issue_repo.get_all()
    
    # GitHub API methods (implementation of GitHubSyncService abstract methods)
    
    async def create_on_github(
        self,
        access_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create issue on GitHub
        
        Args:
            access_token: GitHub access token
            **kwargs: repository_full_name, title, description, labels
        """
        repository_full_name = kwargs.get("repository_full_name")
        if not repository_full_name:
            raise ValueError("repository_full_name is required")
        
        issue_data = {
            "title": kwargs.get("title"),
            "body": kwargs.get("description", ""),
        }
        
        if "labels" in kwargs and kwargs["labels"]:
            issue_data["labels"] = kwargs["labels"]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.github.com/repos/{repository_full_name}/issues",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json=issue_data
            )
            response.raise_for_status()
            return response.json()
    
    async def update_on_github(
        self,
        access_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update issue on GitHub
        
        Args:
            access_token: GitHub access token
            **kwargs: entity_id, title, description, status, labels, repository_full_name (optional)
        """
        # Get issue to find repository and issue number
        entity_id = kwargs.get("entity_id")
        issue = await self.issue_repo.get_by_id(entity_id) if entity_id else None
        
        if not issue:
            raise ValueError("Issue not found")
        
        if not issue.github_issue_number:
            raise ValueError("Issue is not linked to a GitHub issue")
        
        # Get repository_full_name
        repository_full_name = kwargs.get("repository_full_name")
        if not repository_full_name:
            # Look up repository to get full name
            if not self.repo_repository:
                raise ValueError("repository_full_name is required for update when repo_repository is not available")
            
            repository = await self.repo_repository.get_by_id(issue.repository_id)
            if not repository:
                raise ValueError(f"Repository {issue.repository_id} not found")
            repository_full_name = repository.full_name
        
        # Build update payload
        github_updates = {}
        if "title" in kwargs and kwargs["title"] is not None:
            github_updates["title"] = kwargs["title"]
        if "description" in kwargs and kwargs["description"] is not None:
            github_updates["body"] = kwargs["description"]
        if "status" in kwargs and kwargs["status"] is not None:
            github_updates["state"] = kwargs["status"]
        if "labels" in kwargs and kwargs["labels"] is not None:
            github_updates["labels"] = kwargs["labels"]
        
        if not github_updates:
            # No updates to make, return current data as dict
            return issue.model_dump()
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://api.github.com/repos/{repository_full_name}/issues/{issue.github_issue_number}",
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
        entity: Issue,
        **kwargs
    ) -> bool:
        """
        Delete issue on GitHub (not really supported - issues can only be closed)
        
        Args:
            access_token: GitHub access token
            entity: The issue to delete/close
            **kwargs: repository_full_name required
        """
        # GitHub doesn't support deleting issues, only closing them
        # We'll close the issue instead
        logger.info(f"🔍 delete_on_github called for issue {entity.id}")
        
        # Get repository full name
        repository_full_name = kwargs.get("repository_full_name")
        if not repository_full_name:
            # Can't close without repository info
            logger.warning(f"⚠️ Cannot close issue {entity.id} on GitHub: repository_full_name not provided")
            return True  # Return true anyway to allow DB deletion
        
        # Check if issue has a GitHub issue number
        if not entity.github_issue_number:
            logger.warning(f"⚠️ Cannot close issue {entity.id} on GitHub: no github_issue_number")
            return True  # Return true anyway to allow DB deletion
        
        try:
            url = f"https://api.github.com/repos/{repository_full_name}/issues/{entity.github_issue_number}"
            logger.info(f"🚀 Calling GitHub API: PATCH {url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    json={"state": "closed"}
                )
                response.raise_for_status()
                logger.info(f"✅ GitHub API call successful: {response.status_code}")
                return True
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ GitHub API error: {e.response.status_code} - {e.response.text}")
            # If it's a 404, the issue is already gone on GitHub
            if e.response and e.response.status_code == 404:
                logger.info(f"ℹ️ Issue already gone on GitHub (404), continuing with DB deletion")
                return True
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in delete_on_github: {str(e)}")
            raise
    
    # Implementation of SyncableService interface
    
    async def fetch_from_github_api(
        self,
        access_token: str,
        owner: str,
        repo: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch issues from GitHub API without creating DB records
        
        Args:
            access_token: GitHub access token
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of issue data from GitHub API
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
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
        repository_id: str = None,
        owner: str = None,
        repo: str = None,
        **kwargs
    ) -> List[Issue]:
        """
        Synchronize issues from GitHub API to database
        
        Args:
            access_token: GitHub access token
            repository_id: Repository ID in our database
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of synchronized issues
        """
        if not owner or not repo:
            raise ValueError("owner and repo are required")
        
        logger.info(f"Syncing issues for {owner}/{repo}")
        
        # Fetch from GitHub API first
        github_issues = await self.fetch_from_github_api(access_token, owner, repo)
        
        synced_issues = []
        
        for gh_issue in github_issues:
            # Check if issue already exists
            existing_issue = await self.issue_repo.get_by_github_id(gh_issue["id"])
            
            # Map GitHub data to DB format
            issue_data = await self.map_github_to_db(gh_issue)
            
            # Add repository_id if provided
            if repository_id:
                issue_data["repository_id"] = repository_id
            
            if existing_issue:
                # Update existing issue
                issue = await self.issue_repo.update(existing_issue.id, issue_data)
                logger.debug(f"Updated issue #{gh_issue['number']}")
            else:
                # Create new issue
                issue = await self.issue_repo.create(issue_data)
                logger.debug(f"Created issue #{gh_issue['number']}")
            
            synced_issues.append(issue)
        
        logger.info(f"Synced {len(synced_issues)} issues for {owner}/{repo}")
        return synced_issues
    
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

