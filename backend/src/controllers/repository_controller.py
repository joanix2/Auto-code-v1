"""Repository controller - API endpoints for repositories"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.models.repository import Repository, RepositoryCreate
from src.models.user import User
from src.repositories.repository_repository import RepositoryRepository
from src.database import Neo4jConnection
from src.utils.auth import get_current_user

router = APIRouter()


def get_repository_repo():
    """Dependency to get repository repository"""
    db = Neo4jConnection()
    return RepositoryRepository(db)


@router.post("/repositories", response_model=Repository, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo_data: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """Create a new repository"""
    repository = await repo_repo.create_repository(repo_data, current_user.username)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create repository"
        )
    return repository


@router.get("/repositories", response_model=List[Repository])
async def get_repositories(
    current_user: User = Depends(get_current_user),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """Get all repositories for current user"""
    return await repo_repo.get_repositories_by_owner(current_user.username)
