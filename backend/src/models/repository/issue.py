"""
Issue model - GitHub Issues (1 Issue = 1 Branch = 1 PR)
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from ..base import BaseEntity, BaseSemanticModel

IssueStatus = Literal["open", "in_progress", "review", "closed", "cancelled"]
IssuePriority = Literal["low", "medium", "high", "urgent"]
IssueType = Literal["bug", "feature", "documentation", "refactor"]


class Issue(BaseEntity, BaseSemanticModel):
    """Issue model (1 Issue = 1 Branch = 1 PR)"""

    # Relations
    repository_id: str = Field(..., description="Repository ID")
    author_username: str = Field(..., description="Author username")

    # GitHub integration
    github_issue_number: int | None = Field(None, description="GitHub issue number")
    github_issue_url: str | None = Field(None, description="GitHub issue URL")
    github_branch_name: str | None = Field(None, description="Associated branch name")
    github_pr_number: int | None = Field(None, description="GitHub PR number")
    github_pr_url: str | None = Field(None, description="GitHub PR URL")

    # Metadata
    status: IssueStatus = Field(default="open", description="Issue status")
    priority: IssuePriority = Field(default="medium", description="Issue priority")
    issue_type: IssueType = Field(default="feature", description="Issue type")

    # Copilot
    assigned_to_copilot: bool = Field(default=False, description="Assigned to GitHub Copilot")
    copilot_started_at: datetime | None = Field(None, description="When Copilot started working")


class IssueCreate(BaseModel):
    """Data needed to create an issue"""

    title: str
    description: str = ""
    repository_id: str
    priority: IssuePriority = "medium"
    issue_type: IssueType = "feature"


class IssueUpdate(BaseModel):
    """Data for updating an issue"""

    title: str | None = None
    description: str | None = None
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    github_branch_name: str | None = None
    github_pr_number: int | None = None
    github_pr_url: str | None = None
    assigned_to_copilot: bool | None = None
