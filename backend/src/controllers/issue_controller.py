"""
Issue Controller - Manage GitHub issues (1 Issue = 1 Branch = 1 PR)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid
import httpx

from .base_controller import BaseController
from ..models.user import User
from ..models.issue import Issue, IssueCreate, IssueUpdate
from ..repositories.issue_repository import IssueRepository
from ..repositories.repository_repository import RepositoryRepository
from ..services.copilot_agent_service import GitHubCopilotAgentService
from ..services.issue_service import IssueService
from ..utils.auth import get_current_user
from ..utils.error_handler import (
    handle_controller_errors,
    validate_resource_exists,
    validate_authorization
)
from ..database import get_db

router = APIRouter(prefix="/api/issues", tags=["issues"])
logger = logging.getLogger(__name__)


class IssueController(BaseController[Issue, IssueCreate, IssueUpdate]):
    """Issue Controller with CRUD + Sync operations"""
    
    def __init__(self, service: IssueService, repo_repository: RepositoryRepository):
        super().__init__(service.issue_repo)
        self.service = service
        self.repo_repository = repo_repository
    
    def get_resource_name(self) -> str:
        return "issue"
    
    def get_resource_name_plural(self) -> str:
        return "issues"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        return f"issue-{uuid.uuid4()}"
    
    async def validate_create(self, data: IssueCreate, current_user: User, db) -> Dict[str, Any]:
        # Verify repository exists and user has access
        repository = await self.repo_repository.get_by_id(data.repository_id)
        validate_resource_exists(repository, "repository", data.repository_id)
        
        validate_authorization(
            repository.owner_username == current_user.username,
            "Not authorized to create issues in this repository"
        )
        
        # Prepare data with GitHub context for sync
        return {
            "access_token": current_user.github_token,
            "repository_full_name": repository.full_name,
            "title": data.title,
            "description": data.description,
            "labels": [],  # Labels can be added later
            "repository_id": data.repository_id,
            "author_username": current_user.username,
            "status": "open",  # New issues are always open
            "priority": data.priority,
            "issue_type": data.issue_type
        }
    
    async def validate_update(self, resource_id: str, updates: IssueUpdate, current_user: User, db) -> Dict[str, Any]:
        """Validate and prepare update data for service to update on GitHub and DB"""
        issue = await self.service.issue_repo.get_by_id(resource_id)
        validate_resource_exists(issue, "issue", resource_id)
        
        # Get repository for full name (needed for GitHub API)
        repository = await self.repo_repository.get_by_id(issue.repository_id)
        validate_resource_exists(repository, "repository", issue.repository_id)
        
        # Prepare update data with access token and repository full name
        update_data = updates.model_dump(exclude_unset=True)
        update_data["access_token"] = current_user.github_token
        update_data["repository_full_name"] = repository.full_name
        
        return update_data
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Dict[str, Any]:
        """Validate issue deletion and prepare data for GitHub sync"""
        issue = await self.service.issue_repo.get_by_id(resource_id)
        validate_resource_exists(issue, "issue", resource_id)
        
        # Get repository info for GitHub API
        repository = await self.repo_repository.get_by_id(issue.repository_id)
        if not repository or not repository.full_name:
            logger.warning(f"Cannot sync issue {resource_id} deletion to GitHub: repository full_name missing")
            # Return minimal data, will skip GitHub sync
            return {
                "access_token": current_user.github_token,
                "entity_id": resource_id
            }
        
        return {
            "access_token": current_user.github_token,
            "entity_id": resource_id,
            "repository_full_name": repository.full_name
        }
    
    @handle_controller_errors(resource_name="issue", operation="creation")
    async def create(self, data: IssueCreate, current_user: User, db) -> Issue:
        """Create issue with GitHub sync"""
        validated_data = await self.validate_create(data, current_user, db)
        issue = await self.service.create(validated_data)
        return issue
    
    @handle_controller_errors(resource_name="issue", operation="update")
    async def update(self, resource_id: str, updates: IssueUpdate, current_user: User, db) -> Issue:
        """Update issue using service (orchestrates GitHub + DB)"""
        # Validate update (returns data with access_token and repository_full_name)
        validated_updates = await self.validate_update(resource_id, updates, current_user, db)
        
        # Update using service (orchestrates GitHub + DB)
        updated_resource = await self.service.update(resource_id, validated_updates)
        
        validate_resource_exists(updated_resource, "issue", resource_id)
        
        logger.info(f"Updated issue {resource_id}")
        return updated_resource
    
    @handle_controller_errors(resource_name="issue", operation="deletion")
    async def delete(self, resource_id: str, current_user: User, db) -> Dict[str, str]:
        """Delete issue with GitHub sync (closes issue on GitHub)"""
        logger.info(f"🔍 IssueController.delete called for issue_id={resource_id}")
        
        # Validate delete and get data with GitHub context
        validated_data = await self.validate_delete(resource_id, current_user, db)
        logger.info(f"✅ Validation passed. validated_data={validated_data}")
        
        # Extract access_token and entity_id (already passed as resource_id)
        access_token = validated_data.pop("access_token", None)
        validated_data.pop("entity_id", None)  # Remove to avoid duplication with resource_id
        
        logger.info(f"🚀 Calling service.delete with: resource_id={resource_id}, has_token={bool(access_token)}, kwargs={validated_data}")
        
        # Delete using service (orchestrates GitHub + DB)
        await self.service.delete(resource_id, access_token, **validated_data)
        
        logger.info(f"✅ Deleted issue {resource_id}")
        return {"message": "Issue deleted successfully"}
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Issue]:
        """Sync issues from GitHub for a specific repository"""
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        
        if not owner or not repo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner and repo are required for issue sync"
            )
        
        return await self.service.sync_from_github(github_token, owner=owner, repo=repo)
    
    async def get_by_repository(self, repository_id: str, status_filter: Optional[str] = None) -> List[Issue]:
        """Get issues filtered by repository"""
        return await self.service.issue_repo.get_by_repository(repository_id, status_filter)


# Dependency to get controller instance
def get_issue_controller(db = Depends(get_db)) -> IssueController:
    """FastAPI dependency to get IssueController instance"""
    issue_repository = IssueRepository(db)
    repo_repository = RepositoryRepository(db)
    issue_service = IssueService(issue_repository, repo_repository)
    return IssueController(issue_service, repo_repository)


# Route handlers

@router.post("/", response_model=Issue)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: IssueController = Depends(get_issue_controller)
):
    """Create a new issue"""
    return await controller.create(issue_data, current_user, db)


@router.get("/", response_model=List[Issue])
async def list_issues(
    repository_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: IssueController = Depends(get_issue_controller)
):
    """List all issues with optional filters"""
    if repository_id:
        return await controller.get_by_repository(repository_id, status)
    else:
        return await controller.get_all(current_user, db, skip, limit)


@router.get("/{issue_id}", response_model=Issue)
async def get_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: IssueController = Depends(get_issue_controller)
):
    """Get issue by ID"""
    return await controller.get_by_id(issue_id, current_user, db)


@router.patch("/{issue_id}", response_model=Issue)
async def update_issue(
    issue_id: str,
    updates: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: IssueController = Depends(get_issue_controller)
):
    """Update an issue"""
    return await controller.update(issue_id, updates, current_user, db)


@router.delete("/{issue_id}")
async def delete_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: IssueController = Depends(get_issue_controller)
):
    """Delete an issue"""
    return await controller.delete(issue_id, current_user, db)


@router.post("/{issue_id}/assign-to-copilot")
@handle_controller_errors(resource_name="issue", operation="Copilot assignment")
async def assign_to_copilot(
    issue_id: str,
    base_branch: str = "main",
    custom_instructions: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Assign issue to GitHub Copilot Agent
    
    Args:
        issue_id: Issue ID
        base_branch: Base branch for PR
        custom_instructions: Custom instructions for Copilot
        
    Returns:
        Assignment result
    """
    if not current_user.github_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub not connected"
        )
    
    issue_repository = IssueRepository(db)
    repo_repository = RepositoryRepository(db)
    
    # Get issue
    issue = await issue_repository.get_by_id(issue_id)
    validate_resource_exists(issue, "issue", issue_id)
    
    # Get repository
    repository = await repo_repository.get_by_id(issue.repository_id)
    validate_resource_exists(repository, "repository", issue.repository_id)
    
    # Initialize Copilot service
    copilot_service = GitHubCopilotAgentService(current_user.github_token)
    
    # Check Copilot status
    copilot_status = await copilot_service.check_copilot_agent_status(
        repository.owner_username,
        repository.name
    )
    
    if not copilot_status.get("enabled"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub Copilot Agent not enabled for this repository"
        )
    
    # Create or get GitHub issue
    if not issue.github_issue_number:
        # Create GitHub issue first
        from github import Github
        gh = Github(current_user.github_token)
        gh_repo = gh.get_repo(repository.full_name)
        
        gh_issue = gh_repo.create_issue(
            title=issue.title,
            body=issue.description
        )
        
        # Update our issue with GitHub data
        await issue_repository.link_to_github(issue_id, {
            "github_issue_number": gh_issue.number,
            "github_issue_url": gh_issue.html_url
        })
        
        issue = await issue_repository.get_by_id(issue_id)
    
    # Assign to Copilot
    result = await copilot_service.assign_issue_to_copilot(
        owner=repository.owner_username,
        repo=repository.name,
        issue_number=issue.github_issue_number,
        base_branch=base_branch,
        custom_instructions=custom_instructions or issue.description
    )
    
    # Update issue status
    await issue_repository.assign_to_copilot(issue_id)
    
    logger.info(f"Assigned issue {issue_id} to Copilot")
    return result
