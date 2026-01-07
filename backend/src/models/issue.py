"""
Issue model - GitHub Issues (1 Issue = 1 Branch = 1 PR)
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from .base import BaseEntity


IssueStatus = Literal["open", "in_progress", "review", "closed", "cancelled"]
IssuePriority = Literal["low", "medium", "high", "urgent"]
IssueType = Literal["bug", "feature", "documentation", "refactor"]


class Issue(BaseEntity):
    """Issue model (1 Issue = 1 Branch = 1 PR)"""
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Issue description")
    
    # Relations
    repository_id: str = Field(..., description="Repository ID")
    author_username: str = Field(..., description="Author username")
    
    # GitHub integration
    github_issue_number: Optional[int] = Field(None, description="GitHub issue number")
    github_issue_url: Optional[str] = Field(None, description="GitHub issue URL")
    github_branch_name: Optional[str] = Field(None, description="Associated branch name")
    github_pr_number: Optional[int] = Field(None, description="GitHub PR number")
    github_pr_url: Optional[str] = Field(None, description="GitHub PR URL")
    
    # Metadata
    status: IssueStatus = Field(default="open", description="Issue status")
    priority: IssuePriority = Field(default="medium", description="Issue priority")
    issue_type: IssueType = Field(default="feature", description="Issue type")
    
    # Copilot
    assigned_to_copilot: bool = Field(default=False, description="Assigned to GitHub Copilot")
    copilot_started_at: Optional[datetime] = Field(None, description="When Copilot started working")


class IssueCreate(BaseModel):
    """Data needed to create an issue"""
    title: str
    description: str = ""
    repository_id: str
    priority: IssuePriority = "medium"
    issue_type: IssueType = "feature"


class IssueUpdate(BaseModel):
    """Data for updating an issue"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatus] = None
    priority: Optional[IssuePriority] = None
    github_branch_name: Optional[str] = None
    github_pr_number: Optional[int] = None
    github_pr_url: Optional[str] = None
    assigned_to_copilot: Optional[bool] = None
