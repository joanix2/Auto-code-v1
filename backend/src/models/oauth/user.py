"""
User model - OAuth2 Authentication
"""

from pydantic import BaseModel, EmailStr, Field

from ..base import BaseEntity


class User(BaseEntity):
    """User model for OAuth2 authentication"""

    username: str = Field(..., min_length=3, max_length=50, description="GitHub username")
    email: EmailStr | None = Field(None, description="Email address")
    avatar_url: str | None = Field(None, description="Avatar URL")
    github_id: int | None = Field(None, description="GitHub user ID")
    github_token: str | None = Field(
        None, exclude=True, description="GitHub access token (never exposed)"
    )
    is_active: bool = Field(default=True, description="User is active")


class UserPublic(BaseModel):
    """Public user representation (without sensitive data)"""

    id: str
    username: str
    email: EmailStr | None
    avatar_url: str | None
    is_active: bool
    github_token: bool | None = Field(
        None, description="Indicates if GitHub token is set (without exposing it)"
    )

    @staticmethod
    def from_user(user: "User") -> "UserPublic":
        """Create UserPublic from User, hiding the actual token value"""
        return UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            github_token=bool(user.github_token) if hasattr(user, "github_token") else False,
        )


class UserCreate(BaseModel):
    """Data needed to create a user"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr | None = None
    github_id: int | None = None


class UserUpdate(BaseModel):
    """Data for updating a user"""

    email: EmailStr | None = None
    avatar_url: str | None = None
    is_active: bool | None = None
