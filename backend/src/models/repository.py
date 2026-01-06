"""
Repository model - GitHub repositories
"""
from pydantic import BaseModel, Field
from typing import Optional
from .base import BaseEntity


class Repository(BaseEntity):
    """GitHub repository model"""
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="owner/repo")
    owner_username: str = Field(..., description="Owner username")
    description: Optional[str] = Field(None, description="Repository description")
    github_id: Optional[int] = Field(None, description="GitHub repository ID")
    default_branch: str = Field(default="main", description="Default branch")
    is_private: bool = Field(default=False, description="Is private repository")
    
    # Stats
    open_issues_count: int = Field(default=0, description="Number of open issues")


class RepositoryCreate(BaseModel):
    """Data needed to create a repository"""
    name: str
    full_name: str
    owner_username: str
    description: Optional[str] = None
    github_id: Optional[int] = None
    default_branch: str = "main"
    is_private: bool = False


class RepositoryUpdate(BaseModel):
    """Data for updating a repository"""
    name: Optional[str] = None
    description: Optional[str] = None
    default_branch: Optional[str] = None
    open_issues_count: Optional[int] = None

