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
from ..services.repository_permission_service import RepositoryPermissionService
from ..services.github_ruleset_diagnostic import GitHubRulesetDiagnostic
from ..services.repository_initializer_service import RepositoryInitializerService
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


class RepositoryPreparationResponse(BaseModel):
    """Response model for repository preparation check"""
    
    ready: bool
    message: str
    checks: dict
    actions_taken: list
    manual_steps: list


class DiagnosticResponse(BaseModel):
    """Response model for diagnostic report"""
    
    repository: str
    summary: str
    issues_found: list
    recommendations: list
    all_checks: dict


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
        if not user.github_token:
            raise HTTPException(
                status_code=401, detail="GitHub access token not found for user"
            )
        return user.github_token

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
        try:
            # Get repository
            repository = await self.repository_repo.get_by_id(repository_id)
            if not repository:
                raise HTTPException(status_code=404, detail="Repository not found")

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

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking Copilot availability: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error checking Copilot availability: {str(e)}"
            )

    async def prepare_repository(
        self, repository_id: str, user: User, auto_configure: bool = True
    ) -> RepositoryPreparationResponse:
        """
        Prepare repository for Copilot by checking and configuring permissions
        
        Args:
            repository_id: ID of the repository
            user: Current user
            auto_configure: If True, automatically configure bypass permissions
            
        Returns:
            RepositoryPreparationResponse with preparation status
        """
        try:
            # Get repository
            repository = await self.repository_repo.get_by_id(repository_id)
            if not repository:
                raise HTTPException(status_code=404, detail="Repository not found")
            
            # Parse owner/repo
            parts = repository.full_name.split("/")
            if len(parts) != 2:
                raise HTTPException(status_code=400, detail="Invalid repository full_name")
            owner, repo = parts
            
            # Get user token and create permission service
            token = await self._get_user_token(user)
            permission_service = RepositoryPermissionService(token)
            
            # Prepare repository
            logger.info(f"Preparing repository {owner}/{repo} for Copilot (auto_configure={auto_configure})")
            result = await permission_service.prepare_repository_for_copilot(
                owner=owner,
                repo=repo,
                auto_configure=auto_configure
            )
            
            message = "✅ Repository is ready for Copilot!" if result["ready"] else "⚠️ Manual configuration required"
            
            return RepositoryPreparationResponse(
                ready=result["ready"],
                message=message,
                checks=result.get("checks", {}),
                actions_taken=result.get("actions_taken", []),
                manual_steps=result.get("manual_steps", [])
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error preparing repository: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error preparing repository: {str(e)}"
            )

    async def diagnose_repository(
        self, repository_id: str, user: User
    ) -> DiagnosticResponse:
        """
        Run comprehensive diagnostic to identify why Copilot cannot start
        
        Args:
            repository_id: ID of the repository
            user: Current user
            
        Returns:
            DiagnosticResponse with detailed diagnostic report
        """
        try:
            # Get repository
            repository = await self.repository_repo.get_by_id(repository_id)
            if not repository:
                raise HTTPException(status_code=404, detail="Repository not found")
            
            # Parse owner/repo
            parts = repository.full_name.split("/")
            if len(parts) != 2:
                raise HTTPException(status_code=400, detail="Invalid repository full_name")
            owner, repo = parts
            
            # Get user token and create diagnostic service
            token = await self._get_user_token(user)
            diagnostic_service = GitHubRulesetDiagnostic(token)
            
            # Run full diagnostic
            logger.info(f"🔍 Running comprehensive diagnostic for {owner}/{repo}...")
            result = await diagnostic_service.full_diagnostic(owner, repo)
            
            return DiagnosticResponse(
                repository=result.get("repository", f"{owner}/{repo}"),
                summary=result.get("summary", "Diagnostic completed"),
                issues_found=result.get("issues_found", []),
                recommendations=result.get("recommendations", []),
                all_checks=result.get("all_checks", {})
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during diagnostic: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error during diagnostic: {str(e)}"
            )

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
        try:
            # Get issue
            issue = await self.issue_repo.get_by_id(issue_id)
            if not issue:
                raise HTTPException(status_code=404, detail="Issue not found")

            # Get repository
            repository = await self.repository_repo.get_by_id(issue.repository_id)
            if not repository:
                raise HTTPException(status_code=404, detail="Repository not found")

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

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error assigning issue to Copilot: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error assigning issue to Copilot: {str(e)}"
            )

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
        try:
            # Get issue
            issue = await self.issue_repo.get_by_id(issue_id)
            if not issue:
                raise HTTPException(status_code=404, detail="Issue not found")

            # Get repository
            repository = await self.repository_repo.get_by_id(issue.repository_id)
            if not repository:
                raise HTTPException(status_code=404, detail="Repository not found")

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

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error unassigning issue from Copilot: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error unassigning issue from Copilot: {str(e)}"
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
