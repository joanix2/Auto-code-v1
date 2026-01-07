"""
Repository Controller - Manage GitHub repositories
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import logging
import httpx

from .base_controller import BaseController
from ..models.user import User
from ..models.repository import Repository, RepositoryCreate, RepositoryUpdate
from ..repositories.repository_repository import RepositoryRepository
from ..services.repository_service import RepositoryService
from ..repositories.issue_repository import IssueRepository
from ..services.issue_service import IssueService
from ..utils.auth import get_current_user
from ..database import get_db

router = APIRouter(prefix="/api/repositories", tags=["repositories"])
logger = logging.getLogger(__name__)


class RepositoryController(BaseController[Repository, RepositoryCreate, RepositoryUpdate]):
    """Repository Controller with CRUD + Sync + GitHub integration"""
    
    def __init__(self, repository: RepositoryRepository):
        super().__init__(repository)
        self.service = RepositoryService(repository)
    
    def get_resource_name(self) -> str:
        return "repository"
    
    def get_resource_name_plural(self) -> str:
        return "repositories"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        # ID is generated based on GitHub ID
        return data.get("id")  # Already set in validate_create
    
    async def validate_create(self, data: RepositoryCreate, current_user: User, db) -> Dict[str, Any]:
        """Create repository on GitHub first, then prepare data for DB"""
        if not current_user.github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub account not connected. Please connect your GitHub account in your profile settings."
            )
        
        # Create repository on GitHub
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {current_user.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "name": data.name,
                    "description": data.description,
                    "private": data.private,
                }
            )
            
            if response.status_code != 201:
                error_detail = response.json().get("message", "Unknown error")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to create repository on GitHub: {error_detail}"
                )
            
            gh_repo = response.json()
        
        # Prepare data for database
        return {
            "id": f"repo-{gh_repo['id']}",
            "github_id": gh_repo["id"],
            "owner_username": gh_repo["owner"]["login"],
            "name": gh_repo["name"],
            "full_name": gh_repo["full_name"],
            "description": gh_repo.get("description"),
            "is_private": gh_repo["private"],
            "default_branch": gh_repo["default_branch"],
        }
    
    async def validate_update(self, resource_id: str, updates: RepositoryUpdate, current_user: User, db) -> None:
        repository = await self.repository.get_by_id(resource_id)
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
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Repository:
        """Validate and delete from GitHub before DB deletion"""
        repository = await self.repository.get_by_id(resource_id)
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
        
        # Delete from GitHub FIRST
        if current_user.github_token and repository.full_name:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"https://api.github.com/repos/{repository.full_name}",
                    headers={
                        "Authorization": f"Bearer {current_user.github_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code == 204:
                    logger.info(f"Deleted repository {repository.full_name} from GitHub")
                else:
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("message", "Unknown error")
                        logger.error(f"GitHub API error {response.status_code}: {error_data}")
                    except:
                        error_detail = f"HTTP {response.status_code}"
                        logger.error(f"GitHub API error {response.status_code}: Unable to parse response")
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to delete repository from GitHub: {error_detail}"
                    )
        
        return repository
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Repository]:
        """Sync repositories from GitHub"""
        return await self.service.sync_from_github(
            github_token,
            username=current_user.username
        )
    
    async def get_by_owner(self, owner: str, skip: int = 0, limit: int = 100) -> List[Repository]:
        """Get repositories by owner"""
        repositories = await self.repository.get_by_owner(owner)
        return repositories[skip:skip + limit]


# Dependency to get controller instance
def get_repository_controller(db = Depends(get_db)) -> RepositoryController:
    """FastAPI dependency to get RepositoryController instance"""
    repo_repository = RepositoryRepository(db)
    return RepositoryController(repo_repository)


# Route handlers

@router.post("/", response_model=Repository)
async def create_repository(
    repo_data: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: RepositoryController = Depends(get_repository_controller)
):
    """Create a new repository on GitHub and sync to database"""
    return await controller.create(repo_data, current_user, db)


@router.post("/sync")
async def sync_repositories(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: RepositoryController = Depends(get_repository_controller)
):
    """Sync all repositories from GitHub for current user"""
    return await controller.sync(current_user.github_token, current_user, db)


@router.get("/", response_model=List[Repository])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    controller: RepositoryController = Depends(get_repository_controller)
):
    """List all repositories for current user"""
    return await controller.get_by_owner(current_user.username, skip, limit)


@router.get("/{repository_id}", response_model=Repository)
async def get_repository(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: RepositoryController = Depends(get_repository_controller)
):
    """Get repository by ID"""
    repository = await controller.get_by_id(repository_id, current_user, db)
    
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
    db = Depends(get_db),
    controller: RepositoryController = Depends(get_repository_controller)
):
    """Update repository"""
    return await controller.update(repository_id, updates, current_user, db)


@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: RepositoryController = Depends(get_repository_controller)
):
    """Delete repository from GitHub first, then from database"""
    return await controller.delete(repository_id, current_user, db)


@router.post("/{repository_id}/sync-issues")
async def sync_repository_issues(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Sync all issues for a repository from GitHub"""
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
    
    issue_service = IssueService(issue_repository)
    
    try:
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
    except Exception as e:
        logger.error(f"Issue sync error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync issues: {str(e)}"
        )

