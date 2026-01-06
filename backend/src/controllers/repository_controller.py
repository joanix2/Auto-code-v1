"""
Repository Controller - Manage GitHub repositories
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from ..models.user import User
from ..models.repository import Repository, RepositoryCreate, RepositoryUpdate
from ..repositories.repository_repository import RepositoryRepository
from ..services.repository_service import RepositoryService
from ..repositories.issue_repository import IssueRepository
from ..utils.auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/repositories", tags=["repositories"])
logger = logging.getLogger(__name__)


@router.post("/sync")
async def sync_repositories(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Sync all repositories from GitHub for current user
    
    Returns:
        List of synced repositories
    """
    try:
        if not current_user.github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub not connected"
            )
        
        repo_repository = RepositoryRepository(db)
        
        repository_service = RepositoryService(repo_repository)
        
        repositories = await repository_service.sync_from_github(
            current_user.github_token,
            username=current_user.username
        )
        
        logger.info(f"Synced {len(repositories)} repositories for {current_user.username}")
        return {
            "count": len(repositories),
            "repositories": repositories
        }
    except Exception as e:
        logger.error(f"Repository sync error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync repositories: {str(e)}"
        )


@router.get("/", response_model=List[Repository])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List all repositories for current user
    
    Args:
        skip: Number to skip (pagination)
        limit: Maximum number to return
        
    Returns:
        List of repositories
    """
    repo_repository = RepositoryRepository(db)
    repositories = await repo_repository.get_by_owner(current_user.username)
    
    # Apply pagination
    return repositories[skip:skip + limit]


@router.get("/{repository_id}", response_model=Repository)
async def get_repository(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get repository by ID
    
    Args:
        repository_id: Repository ID
        
    Returns:
        Repository details
    """
    repo_repository = RepositoryRepository(db)
    repository = await repo_repository.get_by_id(repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    # Check ownership
    if repository.owner_username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this repository"
        )
    
    return repository


@router.patch("/{repository_id}", response_model=Repository)
async def update_repository(
    repository_id: str,
    updates: RepositoryUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Update repository
    
    Args:
        repository_id: Repository ID
        updates: Fields to update
        
    Returns:
        Updated repository
    """
    repo_repository = RepositoryRepository(db)
    
    # Check existence and ownership
    repository = await repo_repository.get_by_id(repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    if repository.owner_username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this repository"
        )
    
    updated_repository = await repo_repository.update(
        repository_id,
        updates.dict(exclude_unset=True)
    )
    
    return updated_repository


@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete repository
    
    Args:
        repository_id: Repository ID
        
    Returns:
        Success message
    """
    repo_repository = RepositoryRepository(db)
    
    # Check existence and ownership
    repository = await repo_repository.get_by_id(repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    
    if repository.owner_username != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this repository"
        )
    
    deleted = await repo_repository.delete(repository_id)
    
    if deleted:
        return {"message": "Repository deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete repository"
        )


@router.post("/{repository_id}/sync-issues")
async def sync_repository_issues(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Sync all issues for a repository from GitHub
    
    Args:
        repository_id: Repository ID
        
    Returns:
        List of synced issues
    """
    try:
        if not current_user.github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub not connected"
            )
        
        repo_repository = RepositoryRepository(db)
        issue_repository = IssueRepository(db)
        
        # Check repository exists and user owns it
        repository = await repo_repository.get_by_id(repository_id)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        if repository.owner_username != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to sync this repository"
            )
        
        from ..services.issue_service import IssueService
        issue_service = IssueService(issue_repository)
        
        issues = await issue_service.sync_from_github(
            current_user.github_token,
            owner=repository.owner_username,
            repo=repository.name
        )
        
        logger.info(f"Synced {len(issues)} issues for repository {repository_id}")
        return {
            "count": len(issues),
            "issues": issues
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Issue sync error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync issues: {str(e)}"
        )
