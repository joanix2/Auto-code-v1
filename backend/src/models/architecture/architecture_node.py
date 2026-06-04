from typing import Any
from pydantic import BaseModel, Field
from ..dsl import DSLConcept

class ArchitectureNode(DSLConcept):
    dsl_concept_id: str | None = Field(default=None, description="Reference to the DSLConcept that is this node's type")
    properties: dict[str, Any] = Field(default_factory=dict, description="Values for DSLAttributes of the referenced DSLConcept")

class ArchitectureNodeCreate(BaseModel):
    name: str
    description: str | None = None
    dsl_concept_id: str | None = None
    properties: dict[str, Any] = {}

class ArchitectureNodeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    dsl_concept_id: str | None = None
    properties: dict[str, Any] | None = None
