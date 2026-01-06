"""
User model - OAuth2 Authentication
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from .base import BaseEntity


class User(BaseEntity):
    """User model for OAuth2 authentication"""
    username: str = Field(..., min_length=3, max_length=50, description="GitHub username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    github_id: Optional[int] = Field(None, description="GitHub user ID")
    github_token: Optional[str] = Field(None, exclude=True, description="GitHub access token (never exposed)")
    is_active: bool = Field(default=True, description="User is active")


class UserPublic(BaseModel):
    """Public user representation (without sensitive data)"""
    id: str
    username: str
    email: Optional[EmailStr]
    avatar_url: Optional[str]
    is_active: bool


class UserCreate(BaseModel):
    """Data needed to create a user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    github_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Data for updating a user"""
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None

