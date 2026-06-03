"""
Message model - PR comments and conversations
"""

from typing import Literal

from pydantic import BaseModel, Field

from ..base import BaseEntity

MessageAuthorType = Literal["user", "copilot", "system"]


class Message(BaseEntity):
    """Message model (PR comment)"""

    content: str = Field(..., description="Message content")

    # Relations
    issue_id: str = Field(..., description="Issue ID")
    author_username: str | None = Field(None, description="Author username")
    author_type: MessageAuthorType = Field(default="user", description="Author type")

    # GitHub integration
    github_comment_id: int | None = Field(None, description="GitHub comment ID")
    github_comment_url: str | None = Field(None, description="GitHub comment URL")


class MessageCreate(BaseModel):
    """Data needed to create a message"""

    content: str
    issue_id: str
    author_type: MessageAuthorType = "user"


class MessageUpdate(BaseModel):
    """Data for updating a message"""

    content: str | None = None
