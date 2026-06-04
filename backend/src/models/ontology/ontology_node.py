from typing import Any
from pydantic import BaseModel, Field
from ..abstract import AbstractNode

class OntologyNode(AbstractNode):
    node_type_name: str = Field(default="concept", description="Free-form type name")
    
    def get_display_label(self) -> str:
        return self.name or self.node_type_name

class OntologyNodeCreate(BaseModel):
    name: str
    description: str | None = None
    node_type_name: str = "concept"

class OntologyNodeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    node_type_name: str | None = None
