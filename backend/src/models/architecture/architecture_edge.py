from typing import Any
from pydantic import BaseModel, Field
from ..dsl import DSLEdge

class ArchitectureEdge(DSLEdge):
    dsl_edge_type: str | None = Field(default=None, description="Reference to the DSLEdge type")

    def get_edge_type(self) -> str:
        return self.dsl_edge_type or self.edge_type

class ArchitectureEdgeCreate(BaseModel):
    source_id: str
    target_id: str
    edge_type: str = "depends_on"
    dsl_edge_type: str | None = None

class ArchitectureEdgeUpdate(BaseModel):
    edge_type: str | None = None
    dsl_edge_type: str | None = None
