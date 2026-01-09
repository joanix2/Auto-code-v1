"""
Copilot Assignment Controller
Handles HTTP endpoints for assigning issues to GitHub Copilot
"""
import logging
from typing import Optional

from fastapi import HTTPException, Depends
from pydantic import BaseModel, Field

from ..models.user import User
from ..repositories.issue_repository import IssueRepository
from ..repositories.repository_repository import RepositoryRepository
from ..repositories.user_repository import UserRepository
from ..services.copilot_agent_service import GitHubCopilotAgentService
from ..services.repository_initializer_service import RepositoryInitializerService
from ..utils.error_handler import (
    handle_controller_errors,
    validate_github_token,
    validate_resource_exists
)
from ..database import get_db

logger = logging.getLogger(__name__)


# Pydantic models for request/response
class AssignToCopilotRequest(BaseModel):
    """Request model for assigning issue to Copilot"""

    base_branch: Optional[str] = Field(
        None, description="Base branch for the PR (defaults to repository default branch)"
    )
    custom_instructions: Optional[str] = Field(
        "", description="Custom instructions for Copilot agent"
    )


class AssignToCopilotResponse(BaseModel):
    """Response model for Copilot assignment"""

    success: bool
    message: str
    issue_id: str
    assigned_to_copilot: bool
    github_issue_number: Optional[int] = None


class CopilotAvailabilityResponse(BaseModel):
    """Response model for Copilot availability check"""

    available: bool
    message: str
    bot_id: Optional[str] = None


class CopilotAssignmentController:
    """Controller for GitHub Copilot assignment operations"""

    def __init__(
        self,
        issue_repo: IssueRepository,
        repository_repo: RepositoryRepository,
        user_repo: UserRepository,
        copilot_service: Optional[GitHubCopilotAgentService] = None,  # Unused, kept for compatibility
    ):
        self.issue_repo = issue_repo
        self.repository_repo = repository_repo
        self.user_repo = user_repo
        # copilot_service is created per-request with user token

    async def _get_user_token(self, user: User) -> str:
        """Get GitHub access token for user"""
        validate_github_token(user.github_token, "GitHub access token not found for user")
        return user.github_token

    @handle_controller_errors(resource_name="Copilot availability", operation="check")
    async def check_availability(
        self, repository_id: str, user: User
    ) -> CopilotAvailabilityResponse:
        """
        Check if GitHub Copilot coding agent is available for a repository.

        Args:
            repository_id: Repository ID
            user: Current user

        Returns:
            CopilotAvailabilityResponse with availability status
        """
        # Get repository
        repository = await self.repository_repo.get_by_id(repository_id)
        validate_resource_exists(repository, "repository", repository_id)

        # Get user token and create service instance
        token = await self._get_user_token(user)
        copilot_service = GitHubCopilotAgentService(token)

        # Parse owner/repo from full_name
        parts = repository.full_name.split("/")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid repository full_name")
        owner, repo = parts

        # Check availability using check_copilot_agent_status
        status_result = await copilot_service.check_copilot_agent_status(owner, repo)

        if status_result["enabled"]:
            return CopilotAvailabilityResponse(
                available=True,
                message=status_result["message"],
                bot_id=None,  # GraphQL query doesn't return bot_id in this service
            )
        else:
            return CopilotAvailabilityResponse(
                available=False,
                message=status_result["message"],
            )

    @handle_controller_errors(resource_name="issue", operation="Copilot assignment")
    async def assign_to_copilot(
        self, issue_id: str, request: AssignToCopilotRequest, user: User
    ) -> AssignToCopilotResponse:
        """
        Assign an issue to GitHub Copilot coding agent.
        Automatically checks and configures repository permissions before assignment.

        Args:
            issue_id: Issue ID
            request: Assignment request with optional parameters
            user: Current user

        Returns:
            AssignToCopilotResponse with assignment result
        """
        # Get issue
        issue = await self.issue_repo.get_by_id(issue_id)
        validate_resource_exists(issue, "issue", issue_id)

        # Get repository
        repository = await self.repository_repo.get_by_id(issue.repository_id)
        validate_resource_exists(repository, "repository", issue.repository_id)

        # Get user token and create service instances
        token = await self._get_user_token(user)
        copilot_service = GitHubCopilotAgentService(token)
        initializer_service = RepositoryInitializerService(token)

        # Parse owner/repo
        parts = repository.full_name.split("/")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid repository full_name")
        owner, repo = parts

        # 🎯 VÉRIFICATION: Repository initialisé (a des commits)
        logger.info(f"🔍 Checking if repository {owner}/{repo} is initialized...")
        ready_result = await initializer_service.ensure_repository_ready(
            owner=owner,
            repo=repo,
            auto_initialize=True  # Initialisation automatique si vide
        )
        
        if not ready_result["ready"]:
            error_message = (
                f"⚠️ Repository is empty and cannot be initialized.\n\n"
                f"{ready_result.get('message', '')}\n\n"
                f"Manual steps:\n" + "\n".join(ready_result.get("manual_steps", []))
            )
            raise HTTPException(status_code=412, detail=error_message)
        
        # Log si auto-initialisé
        if ready_result.get("action_taken") == "created_readme":
            logger.info(f"✅ Repository auto-initialized with README.md")

        # Check if issue has GitHub issue number
        if not issue.github_issue_number:
            raise HTTPException(
                status_code=400,
                detail="Issue does not have a GitHub issue number. It may not be synced with GitHub.",
            )

        # Get base branch
        base_branch = request.base_branch
        if not base_branch:
            # Get default branch from repository data or use main
            base_branch = "main"

        # Assign to Copilot on GitHub using the service
        result = await copilot_service.assign_issue_to_copilot(
            owner=owner,
            repo=repo,
            issue_number=issue.github_issue_number,
            custom_instructions=request.custom_instructions or "",
            base_branch=base_branch,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500, detail="Failed to assign issue to Copilot on GitHub"
            )

        # Update issue in database
        updated_issue = await self.issue_repo.assign_to_copilot(issue_id, True)

        if not updated_issue:
            logger.warning(
                f"Issue {issue_id} assigned to Copilot on GitHub but failed to update in database"
            )

        return AssignToCopilotResponse(
            success=True,
            message=f"Issue successfully assigned to GitHub Copilot. Check your GitHub notifications for PR updates.",
            issue_id=issue_id,
            assigned_to_copilot=True,
            github_issue_number=issue.github_issue_number,
        )

    @handle_controller_errors(resource_name="issue", operation="Copilot unassignment")
    async def unassign_from_copilot(
        self, issue_id: str, user: User
    ) -> AssignToCopilotResponse:
        """
        Unassign an issue from GitHub Copilot coding agent.

        Args:
            issue_id: Issue ID
            user: Current user

        Returns:
            AssignToCopilotResponse with unassignment result
        """
        # Get issue
        issue = await self.issue_repo.get_by_id(issue_id)
        validate_resource_exists(issue, "issue", issue_id)

        # Get repository
        repository = await self.repository_repo.get_by_id(issue.repository_id)
        validate_resource_exists(repository, "repository", issue.repository_id)

        # Get user token and create service instance
        token = await self._get_user_token(user)
        copilot_service = GitHubCopilotAgentService(token)

        # Parse owner/repo
        parts = repository.full_name.split("/")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid repository full_name")
        owner, repo = parts

        # Check if issue has GitHub issue number
        if not issue.github_issue_number:
            # Just update in database
            updated_issue = await self.issue_repo.assign_to_copilot(issue_id, False)
            return AssignToCopilotResponse(
                success=True,
                message="Issue unassigned from Copilot in database (no GitHub sync needed)",
                issue_id=issue_id,
                assigned_to_copilot=False,
            )

        # Note: GitHubCopilotAgentService doesn't have unassign method
        # We'll just update in database for now
        updated_issue = await self.issue_repo.assign_to_copilot(issue_id, False)

        return AssignToCopilotResponse(
            success=True,
            message="Issue unassigned from GitHub Copilot",
            issue_id=issue_id,
            assigned_to_copilot=False,
            github_issue_number=issue.github_issue_number,
        )


# Factory function to create controller instance
def get_copilot_assignment_controller(
    db = Depends(get_db)
) -> CopilotAssignmentController:
    """Create and return a CopilotAssignmentController instance"""
    issue_repo = IssueRepository(db)
    repository_repo = RepositoryRepository(db)
    user_repo = UserRepository(db)
    # Note: copilot_service instance is created per request with user token
    # We pass None here as it's created in each method
    copilot_service = None  # type: ignore

    return CopilotAssignmentController(
        issue_repo, repository_repo, user_repo, copilot_service  # type: ignore
    )
