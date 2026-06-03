"""
Base models for all entities
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    """Mixin for timestamps"""

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


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
