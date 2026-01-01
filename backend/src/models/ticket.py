"""Ticket model"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status enum"""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class TicketPriority(str, Enum):
    """Ticket priority enum"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TicketType(str, Enum):
    """Ticket type enum"""
    feature = "feature"
    bugfix = "bugfix"
    refactor = "refactor"
    documentation = "documentation"


class TicketBase(BaseModel):
    """Base ticket model"""
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, description="Ticket description")
    repository: str = Field(..., description="Repository full name")
    priority: TicketPriority = Field(default=TicketPriority.medium, description="Ticket priority")
    type: TicketType = Field(default=TicketType.feature, description="Ticket type")


class TicketCreate(TicketBase):
    """Model for creating a ticket"""
    pass


class TicketUpdate(BaseModel):
    """Model for updating a ticket"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None


class Ticket(TicketBase):
    """Complete ticket model"""
    id: str = Field(..., description="Ticket ID")
    status: TicketStatus = Field(default=TicketStatus.pending, description="Ticket status")
    created_by: str = Field(..., description="Username of creator")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
