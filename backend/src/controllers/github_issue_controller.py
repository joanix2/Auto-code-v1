"""GitHub Issue Controller - Handle ticket/issue synchronization"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

from src.database import Neo4jConnection
from src.repositories.ticket_repository import TicketRepository
from src.repositories.repository_repository import RepositoryRepository
from src.services.github.github_issue_service import GitHubIssueService
from src.services.github.github_issue_sync_service import GitHubIssueSyncService
from src.services.auth.github_oauth_service import get_github_token_from_user
from src.controllers.user_controller import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github-issues", tags=["GitHub Issues"])


class CreateIssueRequest(BaseModel):
    """Request model for creating a GitHub issue"""
    ticket_id: str
    branch_name: Optional[str] = None


class UpdateIssueRequest(BaseModel):
    """Request model for updating a GitHub issue"""
    ticket_id: str
    comment: Optional[str] = None


class LinkIssueRequest(BaseModel):
    """Request model for linking an existing GitHub issue"""
    ticket_id: str
    issue_number: int
    issue_url: str


@router.post("/create")
async def create_github_issue_from_ticket(
    request: CreateIssueRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a GitHub issue from a ticket
    
    Args:
        request: Create issue request
        current_user: Current authenticated user
        
    Returns:
        Created issue information
    """
    try:
        # Get GitHub token
        github_token = await get_github_token_from_user(current_user.username)
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub account not connected. Please connect your GitHub account."
            )
        
        # Get ticket
        db = Neo4jConnection()
        ticket_repo = TicketRepository(db)
        ticket = await ticket_repo.get_ticket_by_id(request.ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {request.ticket_id} not found"
            )
        
        # Check if issue already exists
        if ticket.github_issue_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ticket already linked to GitHub issue #{ticket.github_issue_number}"
            )
        
        # Get repository
        repo_repository = RepositoryRepository(db)
        repository = await repo_repository.get_repository_by_id(ticket.repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {ticket.repository_id} not found"
            )
        
        # Create GitHub issue
        github_service = GitHubIssueService(github_token)
        issue_result = github_service.create_issue_from_ticket(
            repo_full_name=repository.full_name,
            ticket=ticket,
            branch_name=request.branch_name
        )
        
        if not issue_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create GitHub issue"
            )
        
        # Link issue to ticket
        await ticket_repo.link_github_issue(
            ticket_id=ticket.id,
            issue_number=issue_result["issue_number"],
            issue_url=issue_result["issue_url"]
        )
        
        logger.info(f"Created GitHub issue #{issue_result['issue_number']} for ticket {ticket.id}")
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "issue_number": issue_result["issue_number"],
            "issue_url": issue_result["issue_url"],
            "message": f"GitHub issue #{issue_result['issue_number']} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating GitHub issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create GitHub issue: {str(e)}"
        )


@router.post("/update-status")
async def update_github_issue_status(
    request: UpdateIssueRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update GitHub issue status based on ticket status
    
    Args:
        request: Update issue request
        current_user: Current authenticated user
        
    Returns:
        Update result
    """
    try:
        # Get GitHub token
        github_token = await get_github_token_from_user(current_user.username)
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub account not connected"
            )
        
        # Get ticket
        db = Neo4jConnection()
        ticket_repo = TicketRepository(db)
        ticket = await ticket_repo.get_ticket_by_id(request.ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {request.ticket_id} not found"
            )
        
        if not ticket.github_issue_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket not linked to any GitHub issue"
            )
        
        # Get repository
        repo_repository = RepositoryRepository(db)
        repository = await repo_repository.get_repository_by_id(ticket.repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {ticket.repository_id} not found"
            )
        
        # Update GitHub issue
        github_service = GitHubIssueService(github_token)
        success = github_service.update_issue_status(
            repo_full_name=repository.full_name,
            issue_number=ticket.github_issue_number,
            ticket_status=ticket.status,
            comment=request.comment
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update GitHub issue"
            )
        
        logger.info(f"Updated GitHub issue #{ticket.github_issue_number} status")
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "issue_number": ticket.github_issue_number,
            "message": "GitHub issue updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating GitHub issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update GitHub issue: {str(e)}"
        )


@router.post("/link")
async def link_existing_github_issue(
    request: LinkIssueRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Link an existing GitHub issue to a ticket
    
    Args:
        request: Link issue request
        current_user: Current authenticated user
        
    Returns:
        Link result
    """
    try:
        # Get ticket
        db = Neo4jConnection()
        ticket_repo = TicketRepository(db)
        ticket = await ticket_repo.get_ticket_by_id(request.ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {request.ticket_id} not found"
            )
        
        # Link issue to ticket
        success = await ticket_repo.link_github_issue(
            ticket_id=ticket.id,
            issue_number=request.issue_number,
            issue_url=request.issue_url
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to link GitHub issue to ticket"
            )
        
        logger.info(f"Linked GitHub issue #{request.issue_number} to ticket {ticket.id}")
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "issue_number": request.issue_number,
            "issue_url": request.issue_url,
            "message": "GitHub issue linked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking GitHub issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to link GitHub issue: {str(e)}"
        )


@router.get("/{ticket_id}/issue-info")
async def get_github_issue_info(
    ticket_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get GitHub issue information for a ticket
    
    Args:
        ticket_id: Ticket ID
        current_user: Current authenticated user
        
    Returns:
        GitHub issue information
    """
    try:
        # Get GitHub token
        github_token = await get_github_token_from_user(current_user.username)
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="GitHub account not connected"
            )
        
        # Get ticket
        db = Neo4jConnection()
        ticket_repo = TicketRepository(db)
        ticket = await ticket_repo.get_ticket_by_id(ticket_id)
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ticket {ticket_id} not found"
            )
        
        if not ticket.github_issue_number:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not linked to any GitHub issue"
            )
        
        # Get repository
        repo_repository = RepositoryRepository(db)
        repository = await repo_repository.get_repository_by_id(ticket.repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {ticket.repository_id} not found"
            )
        
        # Get issue info from GitHub
        github_service = GitHubIssueService(github_token)
        issue_info = github_service.get_issue_info(
            repo_full_name=repository.full_name,
            issue_number=ticket.github_issue_number
        )
        
        if not issue_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GitHub issue #{ticket.github_issue_number} not found"
            )
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "issue": issue_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GitHub issue info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get GitHub issue info: {str(e)}"
        )


@router.get("/sync/{repository_id}")
async def sync_github_issues(
    repository_id: str,
    state: str = "open",
    current_user: dict = Depends(get_current_user)
):
    """
    Get all GitHub issues for a repository
    
    Args:
        repository_id: Repository ID
        state: Issue state filter (open, closed, all)
        current_user: Current authenticated user
        
    Returns:
        List of GitHub issues with import status
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
                detail=f"Repository {repository_id} not found"
            )
        
        # Get existing tickets for this repository
        ticket_repo = TicketRepository(db)
        existing_tickets = await ticket_repo.get_tickets_by_repository(repository_id)
        
        # Get GitHub issues
        sync_service = GitHubIssueSyncService(github_token)
        issues = sync_service.get_repository_issues(
            repo_full_name=repository.full_name,
            state=state
        )
        
        # Check which issues are already imported
        result = []
        for issue in issues:
            existing_ticket = sync_service.check_if_issue_is_imported(
                issue["number"],
                existing_tickets
            )
            
            result.append({
                "issue": issue,
                "is_imported": existing_ticket is not None,
                "ticket_id": existing_ticket.id if existing_ticket else None
            })
        
        logger.info(f"Retrieved {len(result)} issues from {repository.full_name}")
        
        return {
            "success": True,
            "repository_id": repository_id,
            "repository_name": repository.full_name,
            "issues": result,
            "total": len(result),
            "imported": sum(1 for r in result if r["is_imported"]),
            "not_imported": sum(1 for r in result if not r["is_imported"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing GitHub issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync GitHub issues: {str(e)}"
        )


@router.post("/import/{repository_id}/{issue_number}")
async def import_github_issue(
    repository_id: str,
    issue_number: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Import a GitHub issue as a ticket
    
    Args:
        repository_id: Repository ID
        issue_number: GitHub issue number
        current_user: Current authenticated user
        
    Returns:
        Created ticket information
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
                detail=f"Repository {repository_id} not found"
            )
        
        # Check if issue is already imported
        ticket_repo = TicketRepository(db)
        existing_tickets = await ticket_repo.get_tickets_by_repository(repository_id)
        
        sync_service = GitHubIssueSyncService(github_token)
        existing_ticket = sync_service.check_if_issue_is_imported(
            issue_number,
            existing_tickets
        )
        
        if existing_ticket:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"GitHub issue #{issue_number} is already imported as ticket {existing_ticket.id}"
            )
        
        # Get issue from GitHub
        issues = sync_service.get_repository_issues(
            repo_full_name=repository.full_name,
            state="all"
        )
        
        github_issue = next((i for i in issues if i["number"] == issue_number), None)
        if not github_issue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GitHub issue #{issue_number} not found"
            )
        
        # Map GitHub issue to ticket data
        ticket_data = sync_service.map_github_issue_to_ticket_data(
            github_issue,
            repository_id
        )
        
        # Create ticket
        ticket = await ticket_repo.create_ticket(
            ticket_data,
            current_user.username
        )
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create ticket"
            )
        
        # Link GitHub issue to ticket
        await ticket_repo.link_github_issue(
            ticket_id=ticket.id,
            issue_number=issue_number,
            issue_url=github_issue["html_url"]
        )
        
        # Update ticket status based on GitHub state
        github_status = sync_service.map_github_state_to_ticket_status(github_issue["state"])
        if github_status != ticket.status:
            await ticket_repo.update_ticket_status(ticket.id, github_status.value)
        
        logger.info(f"Imported GitHub issue #{issue_number} as ticket {ticket.id}")
        
        return {
            "success": True,
            "ticket_id": ticket.id,
            "issue_number": issue_number,
            "issue_url": github_issue["html_url"],
            "message": f"GitHub issue #{issue_number} imported successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing GitHub issue: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import GitHub issue: {str(e)}"
        )


@router.post("/import-all/{repository_id}")
async def import_all_github_issues(
    repository_id: str,
    state: str = "open",
    current_user: dict = Depends(get_current_user)
):
    """
    Import all GitHub issues from a repository as tickets
    
    Args:
        repository_id: Repository ID
        state: Issue state filter (open, closed, all)
        current_user: Current authenticated user
        
    Returns:
        Import summary
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
                detail=f"Repository {repository_id} not found"
            )
        
        # Get existing tickets
        ticket_repo = TicketRepository(db)
        existing_tickets = await ticket_repo.get_tickets_by_repository(repository_id)
        
        # Get GitHub issues
        sync_service = GitHubIssueSyncService(github_token)
        issues = sync_service.get_repository_issues(
            repo_full_name=repository.full_name,
            state=state
        )
        
        imported = []
        skipped = []
        errors = []
        
        for issue in issues:
            try:
                # Check if already imported
                existing_ticket = sync_service.check_if_issue_is_imported(
                    issue["number"],
                    existing_tickets
                )
                
                if existing_ticket:
                    skipped.append({
                        "issue_number": issue["number"],
                        "ticket_id": existing_ticket.id,
                        "reason": "Already imported"
                    })
                    continue
                
                # Map and create ticket
                ticket_data = sync_service.map_github_issue_to_ticket_data(
                    issue,
                    repository_id
                )
                
                ticket = await ticket_repo.create_ticket(
                    ticket_data,
                    current_user.username
                )
                
                if ticket:
                    # Link GitHub issue
                    await ticket_repo.link_github_issue(
                        ticket_id=ticket.id,
                        issue_number=issue["number"],
                        issue_url=issue["html_url"]
                    )
                    
                    # Update status
                    github_status = sync_service.map_github_state_to_ticket_status(issue["state"])
                    if github_status.value != "open":
                        await ticket_repo.update_ticket_status(ticket.id, github_status.value)
                    
                    imported.append({
                        "issue_number": issue["number"],
                        "ticket_id": ticket.id,
                        "title": issue["title"]
                    })
                    
                    # Add to existing tickets to avoid duplicates
                    existing_tickets.append(ticket)
                
            except Exception as e:
                logger.error(f"Error importing issue #{issue['number']}: {e}")
                errors.append({
                    "issue_number": issue["number"],
                    "error": str(e)
                })
        
        logger.info(f"Imported {len(imported)} issues from {repository.full_name}")
        
        return {
            "success": True,
            "repository_id": repository_id,
            "repository_name": repository.full_name,
            "summary": {
                "total_issues": len(issues),
                "imported": len(imported),
                "skipped": len(skipped),
                "errors": len(errors)
            },
            "imported_tickets": imported,
            "skipped_issues": skipped,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing all GitHub issues: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import GitHub issues: {str(e)}"
        )
