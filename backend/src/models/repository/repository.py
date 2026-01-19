"""
Repository model - GitHub repositories
"""
from pydantic import BaseModel, Field
from typing import Optional
from ..base import BaseSemanticModel


class Repository(BaseSemanticModel):
    """GitHub repository model"""
    full_name: str = Field(..., description="owner/repo")
    owner_username: str = Field(..., description="Owner username")
    github_id: Optional[int] = Field(None, description="GitHub repository ID")
    default_branch: str = Field(default="main", description="Default branch")
    is_private: bool = Field(default=False, description="Is private repository")
    github_created_at: Optional[str] = Field(None, description="Creation timestamp from GitHub")
    github_pushed_at: Optional[str] = Field(None, description="Last push timestamp from GitHub")
    
    # Stats
    open_issues_count: int = Field(default=0, description="Number of open issues")


class RepositoryCreate(BaseModel):
    """Data needed to create a repository"""
    name: str
    description: Optional[str] = None
    private: bool = False


class RepositoryUpdate(BaseModel):
    """Data for updating a repository"""
    name: Optional[str] = None
    description: Optional[str] = None
    default_branch: Optional[str] = None
    open_issues_count: Optional[int] = None

