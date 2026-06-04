from datetime import datetime
from pydantic import BaseModel, Field
from ..base import BaseEntity, BaseSemanticModel


class Project(BaseEntity, BaseSemanticModel):
    status: str = Field(default="draft", description="Project status: draft, active, archived")


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
