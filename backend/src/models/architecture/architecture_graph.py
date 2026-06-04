from typing import Any
from pydantic import BaseModel, Field
from ..dsl import DSLGraph

class ArchitectureGraph(DSLGraph):
    parent_dsl_id: str | None = Field(default=None, description="Reference to parent DSL that constrains this architecture's types")

    @staticmethod
    def get_graph_type() -> str:
        return "architecture"

class ArchitectureGraphCreate(BaseModel):
    name: str
    description: str | None = None
    parent_dsl_id: str | None = None

class ArchitectureGraphUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_dsl_id: str | None = None
