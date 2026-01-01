"""Repository model"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class RepositoryBase(BaseModel):
    """Base repository model"""
    name: str = Field(..., description="Repository name")
    full_name: Optional[str] = Field(None, description="Full repository name (owner/repo)")
    description: Optional[str] = Field(None, description="Repository description")
    github_id: Optional[int] = Field(None, description="GitHub repository ID")
    url: Optional[str] = Field(None, description="Repository URL")
    private: bool = Field(default=False, description="Is private repository")


class RepositoryCreate(RepositoryBase):
    """Model for creating a repository"""
    pass


class RepositoryUpdate(BaseModel):
    """Model for updating a repository"""
    name: Optional[str] = None
    description: Optional[str] = None


class Repository(RepositoryBase):
    """Complete repository model"""
    id: str = Field(..., description="Internal repository ID")
    owner_username: str = Field(..., description="Owner username")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Override to make these fields optional in responses
    full_name: Optional[str] = Field(None, description="Full repository name (owner/repo)")
    github_id: Optional[int] = Field(None, description="GitHub repository ID")
    url: Optional[str] = Field(None, description="Repository URL")
    
    class Config:
        from_attributes = True
