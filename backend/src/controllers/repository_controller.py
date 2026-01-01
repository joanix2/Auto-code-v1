"""Repository controller - API endpoints for repositories"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Optional
from src.models.repository import Repository, RepositoryCreate
from src.models.user import User
from src.repositories.repository_repository import RepositoryRepository
from src.database import Neo4jConnection
from src.utils.auth import get_current_user
from src.services.github_service import GitHubService

router = APIRouter()


def get_repository_repo():
    """Dependency to get repository repository"""
    db = Neo4jConnection()
    return RepositoryRepository(db)


@router.post("/repositories", response_model=Repository, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo_data: RepositoryCreate,
    github_token: Optional[str] = Header(None, alias="X-GitHub-Token"),
    current_user: User = Depends(get_current_user),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """
    Create a new repository on GitHub and save it to the database.
    Requires X-GitHub-Token header with personal access token.
    """
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub token required in X-GitHub-Token header to create repository"
        )
    
    try:
        # Create repository on GitHub first
        github_service = GitHubService(github_token)
        gh_repo = github_service.create_repository(
            name=repo_data.name,
            description=repo_data.description,
            private=repo_data.private
        )
        
        if not gh_repo:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create repository on GitHub"
            )
        
        # Update repo_data with GitHub information
        repo_data.github_id = gh_repo["id"]
        repo_data.url = gh_repo["html_url"]
        repo_data.full_name = gh_repo["full_name"]
        
        # Save to database
        repository = await repo_repo.create_repository(repo_data, current_user.username)
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to save repository to database"
            )
        
        return repository
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create repository: {str(e)}"
        )


@router.get("/repositories", response_model=List[Repository])
async def get_repositories(
    current_user: User = Depends(get_current_user),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """Get all repositories for current user"""
    return await repo_repo.get_repositories_by_owner(current_user.username)


@router.get("/repositories/sync-github")
async def sync_github_repositories(
    github_token: Optional[str] = Header(None, alias="X-GitHub-Token"),
    current_user: User = Depends(get_current_user),
    repo_repo: RepositoryRepository = Depends(get_repository_repo)
):
    """
    Synchronize repositories from GitHub
    Requires X-GitHub-Token header with personal access token
    """
    if not github_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GitHub token required in X-GitHub-Token header"
        )
    
    try:
        github_service = GitHubService(github_token)
        github_repos = await github_service.get_user_repositories()
        
        # Récupérer tous les repos locaux de l'utilisateur
        local_repos = await repo_repo.get_repositories_by_owner(current_user.username)
        
        # Créer un set des github_ids existants sur GitHub
        github_ids = {gh_repo["id"] for gh_repo in github_repos}
        
        # Supprimer les repos qui n'existent plus sur GitHub
        deleted_count = 0
        for local_repo in local_repos:
            if local_repo.github_id and local_repo.github_id not in github_ids:
                await repo_repo.delete_repository(local_repo.id)
                deleted_count += 1
        
        synced_repos = []
        for gh_repo in github_repos:
            # Parser les dates de GitHub
            from dateutil import parser as date_parser
            
            github_created_at = None
            if gh_repo.get("created_at"):
                try:
                    github_created_at = date_parser.parse(gh_repo["created_at"])
                except:
                    pass
            
            github_updated_at = None
            if gh_repo.get("updated_at"):
                try:
                    github_updated_at = date_parser.parse(gh_repo["updated_at"])
                except:
                    pass
            
            github_pushed_at = None
            if gh_repo.get("pushed_at"):
                try:
                    github_pushed_at = date_parser.parse(gh_repo["pushed_at"])
                except:
                    pass
            
            # Créer ou mettre à jour le repository
            repo_data = RepositoryCreate(
                name=gh_repo["name"],
                full_name=gh_repo["full_name"],
                description=gh_repo.get("description"),
                github_id=gh_repo["id"],
                url=gh_repo["html_url"],
                private=gh_repo["private"],
                github_created_at=github_created_at,
                github_updated_at=github_updated_at,
                github_pushed_at=github_pushed_at
            )
            
            # Vérifier si le repo existe déjà
            existing_repo = await repo_repo.get_by_github_id(gh_repo["id"])
            if existing_repo:
                # Mettre à jour
                repository = await repo_repo.update_repository(existing_repo.id, repo_data)
            else:
                # Créer
                repository = await repo_repo.create_repository(repo_data, current_user.username)
            
            if repository:
                synced_repos.append(repository)
        
        return {
            "synced": len(synced_repos),
            "deleted": deleted_count,
            "repositories": synced_repos
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync GitHub repositories: {str(e)}"
        )
