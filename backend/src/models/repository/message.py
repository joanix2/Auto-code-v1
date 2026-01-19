"""
Message model - PR comments and conversations
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from .base import BaseEntity


MessageAuthorType = Literal["user", "copilot", "system"]


class Message(BaseEntity):
    """Message model (PR comment)"""
    content: str = Field(..., description="Message content")
    
    # Relations
    issue_id: str = Field(..., description="Issue ID")
    author_username: Optional[str] = Field(None, description="Author username")
    author_type: MessageAuthorType = Field(default="user", description="Author type")
    
    # GitHub integration
    github_comment_id: Optional[int] = Field(None, description="GitHub comment ID")
    github_comment_url: Optional[str] = Field(None, description="GitHub comment URL")


class MessageCreate(BaseModel):
    """Data needed to create a message"""
    content: str
    issue_id: str
    author_type: MessageAuthorType = "user"


class MessageUpdate(BaseModel):
    """Data for updating a message"""
    content: Optional[str] = None

    content: str
    metadata: Optional[dict] = None
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    step: Optional[str] = None


class MessageUpdate(BaseModel):
    """Schema for updating a message"""
    content: Optional[str] = None
    metadata: Optional[dict] = None
    tokens_used: Optional[int] = None
