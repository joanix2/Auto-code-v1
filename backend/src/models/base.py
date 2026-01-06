"""
Base models for all entities
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TimestampMixin(BaseModel):
    """Mixin for timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class BaseEntity(TimestampMixin):
    """Base for all entities"""
    id: str = Field(..., description="Unique identifier")

    class Config:
        from_attributes = True
