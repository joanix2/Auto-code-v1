"""
Branch Controller
API endpoints for managing ticket branches
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..services.git.branch_service import BranchService
from ..services.git.git_service import GitService
from ..repositories.ticket_repository import TicketRepository
from ..database import db
from ..utils.auth import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/branches", tags=["branches"])


class BranchResponse(BaseModel):
    """Response model for branch operations"""
    branch_name: str
    ticket_id: str
    created: bool
    current: bool


class BranchInfoResponse(BaseModel):
    """Response model for branch information"""
    branch_name: str
    exists: bool
    last_commit: Optional[dict] = None


class BranchListResponse(BaseModel):
    """Response model for listing branches"""
    branches: List[str]
    current_branch: str


@router.post("/ticket/{ticket_id}/ensure", response_model=BranchResponse)
async def ensure_branch_for_ticket(
    ticket_id: str,
    base_branch: str = "main",
    current_user: User = Depends(get_current_user)
) -> BranchResponse:
    """
    Ensure a branch exists for a ticket and checkout to it
    Creates the branch if it doesn't exist, otherwise checks it out
    
    Args:
        ticket_id: Ticket ID
        base_branch: Base branch to create from (default: main)
        current_user: Authenticated user
        
    Returns:
        Branch information
    """
    logger.info(f"User {current_user.username} ensuring branch for ticket {ticket_id}")
    
    # Get ticket
    db.connect()
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    # Get repository URL from ticket
    # Assuming ticket has repository info stored
    from ..repositories.repository_repository import RepositoryRepository
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_repository_by_id(ticket.repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {ticket.repository_id} not found"
        )
    
    # Ensure branch
    branch_service = BranchService()
    try:
        branch_name, was_created = branch_service.ensure_branch_for_ticket(
            ticket, 
            repository.url,
            base_branch=base_branch
        )
        
        current_branch = branch_service.get_current_branch(repository.url)
        
        logger.info(f"Branch {branch_name} {'created' if was_created else 'checked out'} for ticket {ticket_id}")
        
        return BranchResponse(
            branch_name=branch_name,
            ticket_id=ticket_id,
            created=was_created,
            current=current_branch == branch_name
        )
    except Exception as e:
        logger.error(f"Failed to ensure branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ensure branch: {str(e)}"
        )


@router.post("/ticket/{ticket_id}/checkout", response_model=BranchResponse)
async def checkout_ticket_branch(
    ticket_id: str,
    current_user: User = Depends(get_current_user)
) -> BranchResponse:
    """
    Checkout the branch for a ticket (must already exist)
    
    Args:
        ticket_id: Ticket ID
        current_user: Authenticated user
        
    Returns:
        Branch information
    """
    logger.info(f"User {current_user.username} checking out branch for ticket {ticket_id}")
    
    # Get ticket
    db.connect()
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    # Get repository
    from ..repositories.repository_repository import RepositoryRepository
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_repository_by_id(ticket.repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {ticket.repository_id} not found"
        )
    
    # Checkout branch
    branch_service = BranchService()
    try:
        branch_name = branch_service.checkout_ticket_branch(ticket, repository.url)
        current_branch = branch_service.get_current_branch(repository.url)
        
        logger.info(f"Checked out branch {branch_name} for ticket {ticket_id}")
        
        return BranchResponse(
            branch_name=branch_name,
            ticket_id=ticket_id,
            created=False,
            current=current_branch == branch_name
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to checkout branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to checkout branch: {str(e)}"
        )


@router.post("/ticket/{ticket_id}/create", response_model=BranchResponse)
async def create_ticket_branch(
    ticket_id: str,
    base_branch: str = "main",
    force: bool = False,
    current_user: User = Depends(get_current_user)
) -> BranchResponse:
    """
    Create a branch for a ticket
    
    Args:
        ticket_id: Ticket ID
        base_branch: Base branch to create from
        force: If True, recreate branch even if it exists
        current_user: Authenticated user
        
    Returns:
        Branch information
    """
    logger.info(f"User {current_user.username} creating branch for ticket {ticket_id}")
    
    # Get ticket
    db.connect()
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get_ticket_by_id(ticket_id)
    
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )
    
    # Get repository
    from ..repositories.repository_repository import RepositoryRepository
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_repository_by_id(ticket.repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {ticket.repository_id} not found"
        )
    
    # Create branch
    branch_service = BranchService()
    try:
        branch_name = branch_service.create_ticket_branch(
            ticket,
            repository.url,
            base_branch=base_branch,
            force=force
        )
        
        current_branch = branch_service.get_current_branch(repository.url)
        
        logger.info(f"Created branch {branch_name} for ticket {ticket_id}")
        
        return BranchResponse(
            branch_name=branch_name,
            ticket_id=ticket_id,
            created=True,
            current=current_branch == branch_name
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}"
        )


@router.get("/repository/{repository_id}/list", response_model=BranchListResponse)
async def list_ticket_branches(
    repository_id: str,
    current_user: User = Depends(get_current_user)
) -> BranchListResponse:
    """
    List all ticket branches for a repository
    
    Args:
        repository_id: Repository ID
        current_user: Authenticated user
        
    Returns:
        List of branch names
    """
    logger.info(f"User {current_user.username} listing branches for repository {repository_id}")
    
    # Get repository
    db.connect()
    from ..repositories.repository_repository import RepositoryRepository
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_repository_by_id(repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found"
        )
    
    # List branches
    branch_service = BranchService()
    try:
        branches = branch_service.list_ticket_branches(repository.url)
        current_branch = branch_service.get_current_branch(repository.url)
        
        return BranchListResponse(
            branches=branches,
            current_branch=current_branch
        )
    except Exception as e:
        logger.error(f"Failed to list branches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list branches: {str(e)}"
        )


@router.get("/info/{branch_name:path}", response_model=BranchInfoResponse)
async def get_branch_info(
    branch_name: str,
    repository_id: str,
    current_user: User = Depends(get_current_user)
) -> BranchInfoResponse:
    """
    Get information about a branch
    
    Args:
        branch_name: Branch name
        repository_id: Repository ID
        current_user: Authenticated user
        
    Returns:
        Branch information
    """
    logger.info(f"User {current_user.username} getting info for branch {branch_name}")
    
    # Get repository
    db.connect()
    from ..repositories.repository_repository import RepositoryRepository
    repo_repo = RepositoryRepository(db)
    repository = await repo_repo.get_repository_by_id(repository_id)
    
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found"
        )
    
    # Get branch info
    branch_service = BranchService()
    try:
        info = branch_service.get_branch_info(repository.url, branch_name)
        
        return BranchInfoResponse(**info)
    except Exception as e:
        logger.error(f"Failed to get branch info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get branch info: {str(e)}"
        )
