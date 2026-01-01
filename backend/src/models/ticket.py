"""Ticket model"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status enum"""
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
    cancelled = "cancelled"


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
    description: Optional[str] = Field(None, description="Ticket description")
    priority: TicketPriority = Field(default=TicketPriority.medium, description="Ticket priority")
    ticket_type: TicketType = Field(default=TicketType.feature, description="Ticket type", alias="type")


class TicketCreate(BaseModel):
    """Model for creating a ticket"""
    model_config = ConfigDict(populate_by_name=True)
    
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: Optional[str] = Field(None, description="Ticket description")
    repository_id: str = Field(..., description="Repository ID")
    priority: TicketPriority = Field(default=TicketPriority.medium, description="Ticket priority")
    ticket_type: TicketType = Field(default=TicketType.feature, description="Ticket type", alias="type")


class TicketUpdate(BaseModel):
    """Model for updating a ticket"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None


class Ticket(TicketBase):
    """Complete ticket model"""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    id: str = Field(..., description="Ticket ID")
    repository_id: str = Field(..., description="Repository ID")
    repository_name: Optional[str] = Field(None, description="Repository name")
    status: TicketStatus = Field(default=TicketStatus.open, description="Ticket status")
    created_by: str = Field(..., description="Username of creator")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
