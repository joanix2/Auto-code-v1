from typing import Any
from pydantic import BaseModel, Field
from ..abstract import AbstractGraph

class OntologyGraph(AbstractGraph):
    @staticmethod
    def get_graph_type() -> str:
        return "ontology"

class OntologyGraphCreate(BaseModel):
    name: str
    description: str | None = None

class OntologyGraphUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
