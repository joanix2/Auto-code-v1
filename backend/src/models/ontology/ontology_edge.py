from typing import Any
from pydantic import BaseModel, Field
from ..abstract import AbstractEdge

class OntologyEdge(AbstractEdge):
    def get_edge_type(self) -> str:
        return self.edge_type
    def get_display_label(self) -> str:
        return self.edge_type
    def is_directed(self) -> bool:
        return True

class OntologyEdgeCreate(BaseModel):
    source_id: str
    target_id: str
    edge_type: str = "related_to"

class OntologyEdgeUpdate(BaseModel):
    edge_type: str | None = None
