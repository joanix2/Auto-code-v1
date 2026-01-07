"""
Copilot Assignment Routes
API endpoints for GitHub Copilot issue assignment
"""
from fastapi import APIRouter, Depends

from ..models.user import User
from ..controllers.copilot_assignment_controller import (
    AssignToCopilotRequest,
    AssignToCopilotResponse,
    CopilotAssignmentController,
    CopilotAvailabilityResponse,
    RepositoryPreparationResponse,
    DiagnosticResponse,
    get_copilot_assignment_controller,
)
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/copilot", tags=["Copilot Assignment"])


@router.get(
    "/availability/{repository_id}",
    response_model=CopilotAvailabilityResponse,
    summary="Check Copilot availability",
    description="Check if GitHub Copilot coding agent is available for a repository",
)
async def check_copilot_availability(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    controller: CopilotAssignmentController = Depends(get_copilot_assignment_controller),
):
    """Check if GitHub Copilot coding agent is available for the repository"""
    return await controller.check_availability(repository_id, current_user)


@router.get(
    "/prepare/{repository_id}",
    response_model=RepositoryPreparationResponse,
    summary="Prepare repository for Copilot",
    description="Check and automatically configure repository permissions for Copilot",
)
async def prepare_repository_for_copilot(
    repository_id: str,
    auto_configure: bool = True,
    current_user: User = Depends(get_current_user),
    controller: CopilotAssignmentController = Depends(get_copilot_assignment_controller),
):
    """
    Prepare repository for Copilot by checking and configuring permissions.
    
    This endpoint:
    - Verifies OAuth token has required scopes
    - Checks repository rulesets
    - Detects incompatible rules (e.g., required signatures)
    - Automatically adds Copilot to bypass list if auto_configure=True
    
    Returns detailed status and manual steps if configuration fails.
    """
    return await controller.prepare_repository(repository_id, current_user, auto_configure)


@router.get(
    "/diagnose/{repository_id}",
    response_model=DiagnosticResponse,
    summary="Diagnose repository issues",
    description="Run comprehensive diagnostic to identify why Copilot cannot start",
)
async def diagnose_repository_issues(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    controller: CopilotAssignmentController = Depends(get_copilot_assignment_controller),
):
    """
    Run comprehensive diagnostic on repository to identify issues.
    
    This endpoint checks:
    - Repository-level rulesets and bypass permissions
    - Organization-level rulesets (inherited)
    - Legacy branch protection rules
    - Copilot app permissions
    - Problematic rules (required signatures, linear history, etc.)
    
    Returns detailed report with issues found and recommendations.
    """
    return await controller.diagnose_repository(repository_id, current_user)


@router.post(
    "/assign/{issue_id}",
    response_model=AssignToCopilotResponse,
    summary="Assign issue to Copilot",
    description="Assign an issue to GitHub Copilot coding agent to automatically create a PR",
)
async def assign_issue_to_copilot(
    issue_id: str,
    request: AssignToCopilotRequest,
    current_user: User = Depends(get_current_user),
    controller: CopilotAssignmentController = Depends(get_copilot_assignment_controller),
):
    """Assign an issue to GitHub Copilot coding agent"""
    return await controller.assign_to_copilot(issue_id, request, current_user)


@router.delete(
    "/assign/{issue_id}",
    response_model=AssignToCopilotResponse,
    summary="Unassign issue from Copilot",
    description="Remove GitHub Copilot coding agent assignment from an issue",
)
async def unassign_issue_from_copilot(
    issue_id: str,
    current_user: User = Depends(get_current_user),
    controller: CopilotAssignmentController = Depends(get_copilot_assignment_controller),
):
    """Unassign an issue from GitHub Copilot coding agent"""
    return await controller.unassign_from_copilot(issue_id, current_user)
