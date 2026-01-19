"""
Base models for all entities
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class TimestampMixin(BaseModel):
    """Mixin for timestamps"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class BaseEntity(TimestampMixin):
    """Base for all entities"""
    id: str = Field(..., description="Unique identifier")

    class Config:
        from_attributes = True

class GenderType(str, Enum):
    """Gender for grammatical articles"""
    MASCULIN = "m"
    FEMININ = "f"
    NEUTRE = "n"


class BaseSemanticModel(BaseModel):
    """Base model for all semantic types - just name and description"""
    name: str = Field(..., description="Unique identifier name")
    description: str = Field(default="", description="Human-readable description")