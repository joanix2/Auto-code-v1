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
        # ID is generated in the service from GitHub ID
        return data.get("id", "")  # Will be set by service
    
    async def create(self, data: RepositoryCreate, current_user: User, db) -> Repository:
        """Create repository using service (orchestrates GitHub + DB)"""
        try:
            # Validate and prepare data
            validated_data = await self.validate_create(data, current_user, db)
            
            # Create using service (orchestrates GitHub + DB)
            resource = await self.service.create(validated_data)
            logger.info(f"Created repository {resource.id}")
            
            return resource
            
        except HTTPException:
            raise
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("message", "Unknown error") if e.response else str(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create repository on GitHub: {error_detail}"
            )
        except Exception as e:
            logger.error(f"Repository creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create repository: {str(e)}"
            )
    
    async def update(self, resource_id: str, updates: RepositoryUpdate, current_user: User, db) -> Repository:
        """Update repository using service (orchestrates GitHub + DB)"""
        try:
            # Validate update (returns data with access_token)
            validated_updates = await self.validate_update(resource_id, updates, current_user, db)
            
            # Update using service (orchestrates GitHub + DB)
            updated_resource = await self.service.update(resource_id, validated_updates)
            
            logger.info(f"Updated repository {resource_id}")
            return updated_resource
            
        except HTTPException:
            raise
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("message", "Unknown error") if e.response else str(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update repository on GitHub: {error_detail}"
            )
        except Exception as e:
            logger.error(f"Repository update error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update repository: {str(e)}"
            )
    
    async def validate_create(self, data: RepositoryCreate, current_user: User, db) -> Dict[str, Any]:
        """Prepare data for service to create repository on GitHub and DB"""
        if not current_user.github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub account not connected. Please connect your GitHub account in your profile settings."
            )
        
        # Return data with access_token for service to use
        return {
            "access_token": current_user.github_token,
            "name": data.name,
            "description": data.description,
            "private": data.private
        }
    
    async def validate_update(self, resource_id: str, updates: RepositoryUpdate, current_user: User, db) -> Dict[str, Any]:
        """Prepare update data for service to update on GitHub and DB"""
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
        
        if not current_user.github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub account not connected"
            )
        
        # Prepare data with access_token for service
        update_data = updates.model_dump(exclude_unset=True)
        update_data["access_token"] = current_user.github_token
        return update_data
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Repository:
        """Validate delete operation"""
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
        
        return repository
    
    async def delete(self, resource_id: str, current_user: User, db) -> Dict[str, str]:
        """Delete repository from GitHub and database using service"""
        try:
            # Validate delete
            repository = await self.validate_delete(resource_id, current_user, db)
            
            # Delete using service (orchestrates GitHub + DB)
            deleted = await self.service.delete(
                entity_id=resource_id,
                access_token=current_user.github_token
            )
            
            if deleted:
                logger.info(f"Deleted repository {resource_id}")
                return {"message": "Repository deleted successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete repository"
                )
        
        except HTTPException:
            raise
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("message", "Unknown error") if e.response else str(e)
            logger.error(f"GitHub API error: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete repository from GitHub: {error_detail}"
            )
        except Exception as e:
            logger.error(f"Repository delete error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete repository: {str(e)}"
            )
    
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

