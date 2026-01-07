"""
Issue Controller - Manage GitHub issues (1 Issue = 1 Branch = 1 PR)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import uuid

from .base_controller import BaseController
from ..models.user import User
from ..models.issue import Issue, IssueCreate, IssueUpdate
from ..repositories.issue_repository import IssueRepository
from ..repositories.repository_repository import RepositoryRepository
from ..services.copilot_agent_service import GitHubCopilotAgentService
from ..services.issue_service import IssueService
from ..utils.auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/issues", tags=["issues"])
logger = logging.getLogger(__name__)


class IssueController(BaseController[Issue, IssueCreate, IssueUpdate]):
    """Issue Controller with CRUD + Sync operations"""
    
    def __init__(self, repository: IssueRepository, repo_repository: RepositoryRepository):
        super().__init__(repository)
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
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        if repository.owner_username != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create issues in this repository"
            )
        
        # Prepare data
        validated_data = data.dict()
        validated_data["author_username"] = current_user.username
        return validated_data
    
    async def validate_update(self, resource_id: str, updates: IssueUpdate, current_user: User, db) -> None:
        issue = await self.repository.get_by_id(resource_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )
        return None  # No modified data to return
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Issue:
        issue = await self.repository.get_by_id(resource_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )
        return issue
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Issue]:
        """Sync issues from GitHub for a specific repository"""
        owner = kwargs.get("owner")
        repo = kwargs.get("repo")
        
        if not owner or not repo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Owner and repo are required for issue sync"
            )
        
        issue_service = IssueService(self.repository)
        return await issue_service.sync_from_github(github_token, owner=owner, repo=repo)
    
    async def get_by_repository(self, repository_id: str, status_filter: Optional[str] = None) -> List[Issue]:
        """Get issues filtered by repository"""
        return await self.repository.get_by_repository(repository_id, status_filter)


# Dependency to get controller instance
def get_issue_controller(db = Depends(get_db)) -> IssueController:
    """FastAPI dependency to get IssueController instance"""
    issue_repository = IssueRepository(db)
    repo_repository = RepositoryRepository(db)
    return IssueController(issue_repository, repo_repository)


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
    try:
        if not current_user.github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub not connected"
            )
        
        issue_repository = IssueRepository(db)
        repo_repository = RepositoryRepository(db)
        
        # Get issue
        issue = await issue_repository.get_by_id(issue_id)
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Issue not found"
            )
        
        # Get repository
        repository = await repo_repository.get_by_id(issue.repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Copilot assignment error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign to Copilot: {str(e)}"
        )
