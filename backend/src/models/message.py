"""
Message Model
Represents a message in a conversation with LLM for a ticket
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Message(BaseModel):
    """
    Message in a ticket conversation
    Stores LLM interactions and responses
    """
    id: str
    ticket_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict] = None  # For storing additional context
    
    # LLM-specific fields
    model: Optional[str] = None  # e.g., "claude-opus-4-20250514"
    tokens_used: Optional[int] = None
    step: Optional[str] = None  # e.g., "analysis", "code_generation", "review"
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_abc123",
                "ticket_id": "ticket_xyz789",
                "role": "assistant",
                "content": "I've analyzed the requirements and created a development plan...",
                "timestamp": "2026-01-02T10:30:00",
                "metadata": {
                    "iteration": 1,
                    "workflow_type": "standard"
                },
                "model": "claude-opus-4-20250514",
                "tokens_used": 1250,
                "step": "analysis"
            }
        }


class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    ticket_id: str
    role: str
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
