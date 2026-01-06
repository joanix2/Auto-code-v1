"""
Issue Controller - Manage GitHub issues (1 Issue = 1 Branch = 1 PR)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
import logging

from ..models.user import User
from ..models.issue import Issue, IssueCreate, IssueUpdate
from ..repositories.issue_repository import IssueRepository
from ..repositories.repository_repository import RepositoryRepository
from ..services.github import GitHubCopilotAgentService
from ..utils.auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/issues", tags=["issues"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=Issue)
async def create_issue(
    issue_data: IssueCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new issue
    
    Args:
        issue_data: Issue creation data
        
    Returns:
        Created issue
    """
    import uuid
    
    issue_repository = IssueRepository(db)
    repo_repository = RepositoryRepository(db)
    
    # Verify repository exists and user has access
    repository = await repo_repository.get_by_id(issue_data.repository_id)
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
    
    # Create issue
    data = issue_data.dict()
    data["id"] = f"issue-{uuid.uuid4()}"
    data["author_username"] = current_user.username
    
    issue = await issue_repository.create(data)
    logger.info(f"Created issue {issue.id} in repository {repository.name}")
    
    return issue


@router.get("/", response_model=List[Issue])
async def list_issues(
    repository_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List all issues
    
    Args:
        repository_id: Filter by repository ID
        status: Filter by status
        skip: Number to skip (pagination)
        limit: Maximum number to return
        
    Returns:
        List of issues
    """
    issue_repository = IssueRepository(db)
    
    if repository_id:
        issues = await issue_repository.get_by_repository(repository_id, status)
    else:
        issues = await issue_repository.get_all(skip, limit)
    
    return issues


@router.get("/{issue_id}", response_model=Issue)
async def get_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get issue by ID
    
    Args:
        issue_id: Issue ID
        
    Returns:
        Issue details
    """
    issue_repository = IssueRepository(db)
    issue = await issue_repository.get_by_id(issue_id)
    
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    return issue


@router.patch("/{issue_id}", response_model=Issue)
async def update_issue(
    issue_id: str,
    updates: IssueUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Update an issue
    
    Args:
        issue_id: Issue ID
        updates: Fields to update
        
    Returns:
        Updated issue
    """
    issue_repository = IssueRepository(db)
    
    issue = await issue_repository.get_by_id(issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    updated_issue = await issue_repository.update(
        issue_id,
        updates.dict(exclude_unset=True)
    )
    
    return updated_issue


@router.delete("/{issue_id}")
async def delete_issue(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete an issue
    
    Args:
        issue_id: Issue ID
        
    Returns:
        Success message
    """
    issue_repository = IssueRepository(db)
    
    issue = await issue_repository.get_by_id(issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )
    
    deleted = await issue_repository.delete(issue_id)
    
    if deleted:
        return {"message": "Issue deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete issue"
        )


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
