"""
Copilot Development Controller
Gère le développement automatique via GitHub Copilot Agent
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

from ..models.user import User
from ..models.ticket import Ticket
from ..repositories.ticket_repository import TicketRepository
from ..repositories.repository_repository import RepositoryRepository
from ..services.github.copilot_agent_service import GitHubCopilotAgentService
from ..services.auth.github_oauth_service import get_github_token_from_user
from ..database import Neo4jConnection
from ..utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class StartDevelopmentRequest(BaseModel):
    """Request to start development with Copilot"""
    ticket_id: str
    custom_instructions: Optional[str] = None
    base_branch: Optional[str] = "main"
    model: Optional[str] = None


class StartDevelopmentResponse(BaseModel):
    """Response from starting development"""
    success: bool
    ticket_id: str
    issue_number: Optional[int] = None
    issue_url: Optional[str] = None
    message: str


@router.post("/start-development", response_model=StartDevelopmentResponse)
async def start_copilot_development(
    request: StartDevelopmentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Start automatic development using GitHub Copilot Agent
    
    This endpoint:
    1. Gets the ticket details
    2. Creates or updates a GitHub issue
    3. Assigns the issue to Copilot coding agent
    4. Updates the ticket status to in_progress
    
    Args:
        request: Development request
        current_user: Current authenticated user
        
    Returns:
        Development start confirmation
    """
    try:
        # Get GitHub token
        github_token = await get_github_token_from_user(current_user.username)
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub account not connected. Please connect your GitHub account in settings."
            )
        
        # Get ticket
        db = Neo4jConnection()
        ticket_repo = TicketRepository(db)
        ticket = await ticket_repo.get_ticket_by_id(request.ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        logger.info(f"Processing ticket {ticket.id} with repository_id: {ticket.repository_id}")
        
        # Get repository
        repo_repository = RepositoryRepository(db)
        repository = await repo_repository.get_repository_by_id(ticket.repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        logger.info(f"Found repository: {repository.name}, full_name: {getattr(repository, 'full_name', None)}")
        
        # Parse owner/repo from repository name or URL
        if repository.full_name:
            parts = repository.full_name.split("/")
            if len(parts) == 2:
                owner, repo_name = parts
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid repository format. Expected 'owner/repo'"
                )
        else:
            # Construct from owner_username and name
            if hasattr(repository, 'owner_username') and repository.owner_username:
                owner = repository.owner_username
                repo_name = repository.name
                logger.info(f"Constructed owner/repo from owner_username: {owner}/{repo_name}")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Repository full_name not set and owner_username not available"
                )
        
        # Initialize Copilot service
        copilot_service = GitHubCopilotAgentService(github_token)
        
        # Check if Copilot is enabled for this repository
        copilot_status = await copilot_service.check_copilot_agent_status(owner, repo_name)
        if not copilot_status["enabled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub Copilot Agent is not enabled for this repository. Please ensure you have an active GitHub Copilot subscription and that the Copilot Agent feature is enabled for your account. Visit https://github.com/features/copilot for more information."
            )
        
        assignee_name = copilot_status.get("assignee_name", "Copilot")
        logger.info(f"Using Copilot assignee: {assignee_name}")
        
        # Build custom instructions from ticket
        instructions = f"""
**Ticket Details:**
- Title: {ticket.title}
- Type: {ticket.ticket_type}
- Priority: {ticket.priority}

**Description:**
{ticket.description}
"""
        
        if request.custom_instructions:
            instructions += f"\n\n**Additional Instructions:**\n{request.custom_instructions}"
        
        # Check if ticket already has a GitHub issue
        if ticket.github_issue_number and ticket.github_issue_url:
            # Assign existing issue to Copilot
            logger.info(f"Assigning existing issue #{ticket.github_issue_number} to Copilot")
            result = await copilot_service.assign_issue_to_copilot(
                owner=owner,
                repo=repo_name,
                issue_number=ticket.github_issue_number,
                custom_instructions=instructions,
                base_branch=request.base_branch,
                model=request.model,
                assignee_name=assignee_name
            )
            
            issue_number = ticket.github_issue_number
            issue_url = ticket.github_issue_url
        else:
            # Create new issue and assign to Copilot
            logger.info(f"Creating new issue for ticket {ticket.id}")
            
            # Build labels from ticket metadata
            labels = []
            if ticket.ticket_type == "bugfix":
                labels.append("bug")
            elif ticket.ticket_type == "feature":
                labels.append("enhancement")
            elif ticket.ticket_type == "documentation":
                labels.append("documentation")
            
            # Add priority label
            labels.append(f"priority: {ticket.priority}")
            labels.append("autocode")
            
            result = await copilot_service.create_issue_and_assign_to_copilot(
                owner=owner,
                repo=repo_name,
                title=ticket.title,
                body=ticket.description,
                custom_instructions=instructions,
                base_branch=request.base_branch,
                labels=labels,
                model=request.model,
                assignee_name=assignee_name
            )
            
            issue_number = result["issue_number"]
            issue_url = result["issue_url"]
            
            # Link the issue to the ticket
            await ticket_repo.link_github_issue(
                ticket_id=ticket.id,
                issue_number=issue_number,
                issue_url=issue_url
            )
        
        # Update ticket status to in_progress
        from ..models.ticket import TicketStatus
        await ticket_repo.update_ticket(
            ticket_id=ticket.id,
            updates={"status": TicketStatus.IN_PROGRESS}
        )
        
        logger.info(f"Successfully started Copilot development for ticket {ticket.id}")
        
        return StartDevelopmentResponse(
            success=True,
            ticket_id=ticket.id,
            issue_number=issue_number,
            issue_url=issue_url,
            message=f"GitHub Copilot is now working on issue #{issue_number}. You will be notified when the PR is ready for review."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Copilot development: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start development: {str(e)}"
        )


@router.get("/check-copilot-status/{repository_id}")
async def check_copilot_status(
    repository_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check if Copilot coding agent is enabled for a repository
    
    Args:
        repository_id: Repository ID
        current_user: Current authenticated user
        
    Returns:
        Copilot status
    """
    try:
        # Get GitHub token
        github_token = await get_github_token_from_user(current_user.username)
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub account not connected"
            )
        
        # Get repository
        db = Neo4jConnection()
        repo_repository = RepositoryRepository(db)
        repository = await repo_repository.get_repository_by_id(repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Repository not found"
            )
        
        # Parse owner/repo
        if repository.full_name:
            parts = repository.full_name.split("/")
            if len(parts) == 2:
                owner, repo_name = parts
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid repository format"
                )
        else:
            # Construct from owner_username and name
            if hasattr(repository, 'owner_username') and repository.owner_username:
                owner = repository.owner_username
                repo_name = repository.name
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Repository full_name not set and owner_username not available"
                )
        
        # Check Copilot status
        copilot_service = GitHubCopilotAgentService(github_token)
        result = await copilot_service.check_copilot_agent_status(owner, repo_name)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking Copilot status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check Copilot status: {str(e)}"
        )
