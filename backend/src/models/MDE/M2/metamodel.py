"""
Metamodel Model - Container for concepts and relationships (MDE ontology)
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from ...graph import Graph
from ...graph.edge_type import EdgeType
from ..M3.m3_config import EDGE_TYPES, NODE_TYPES

# Enums - Keep Literal for backward compatibility
MetamodelStatus = Literal["draft", "validated", "deprecated"]


class Metamodel(Graph):
    """
    Metamodel - A graph containing concepts and relationships

    A metamodel defines:
    - The structure of a domain (concepts/classes as nodes)
    - The relationships between concepts (as edges)
    - Constraints and rules
    - Can be used to generate code, validate models, etc.

    Inherits from Graph:
    - name, description (from Graph)
    - node_count, edge_count (from Graph)
    - owner_id (from Graph)
    - allowed_node_types, allowed_edge_types (from Graph)
    """

    version: str = Field(..., min_length=1, max_length=50, description="Metamodel version")
    status: MetamodelStatus = Field(default="draft", description="Metamodel status")
    repository_id: str | None = Field(default=None, description="GitHub repository ID")

    def __init__(self, **data):
        """Initialize metamodel with M3 type constraints"""
        # Set allowed types from M3 configuration if not provided
        if "allowed_node_types" not in data:
            data["allowed_node_types"] = NODE_TYPES
        if "allowed_edge_types" not in data:
            data["allowed_edge_types"] = EDGE_TYPES
        super().__init__(**data)

    # Abstract methods implementation
    def get_graph_type(self) -> str:
        """Return 'metamodel' as the graph type"""
        return "metamodel"

    class Config:
        from_attributes = True


# Base Model for Create/Update operations
class MetamodelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    version: str = Field(..., min_length=1, max_length=50)
    node_count: int = Field(default=0, ge=0, description="Number of concepts")
    edge_count: int = Field(default=0, ge=0, description="Number of relationships")

    # Backward compatibility aliases
    @property
    def concepts(self) -> int:
        """Alias for node_count (backward compatibility)"""
        return self.node_count

    @property
    def relations(self) -> int:
        """Alias for edge_count (backward compatibility)"""
        return self.edge_count

    author: str | None = None
    status: MetamodelStatus = "draft"


# Create Model
class MetamodelCreate(MetamodelBase):
    type: str | None = "custom"
    documentation: str | None = None
    namespace: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    repository_id: str | None = None
    repository_path: str | None = None


# Update Model
class MetamodelUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    version: str | None = Field(None, min_length=1, max_length=50)
    node_count: int | None = Field(None, ge=0, description="Number of concepts")
    edge_count: int | None = Field(None, ge=0, description="Number of relationships")

    # Backward compatibility - accept old field names
    concepts: int | None = Field(None, ge=0, deprecated=True)
    relations: int | None = Field(None, ge=0, deprecated=True)

    author: str | None = None
    status: MetamodelStatus | None = None
    type: str | None = None
    documentation: str | None = None
    namespace: str | None = None
    settings: dict[str, Any] | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None
    collaborators: list[str] | None = None
    is_public: bool | None = None
    repository_path: str | None = None


class MetamodelResponse(Metamodel):
    """Schema for metamodel response - includes all Metamodel fields"""

    pass


class MetamodelWithDetails(Metamodel):
    """Extended metamodel response with concepts and relationships"""

    concept_list: list[dict[str, Any]] = Field(
        default_factory=list, description="List of concept details"
    )
    relationship_list: list[dict[str, Any]] = Field(
        default_factory=list, description="List of relationship details"
    )

    class Config:
        from_attributes = True


class MetamodelGraphResponse(BaseModel):
    """Response schema for metamodel graph endpoint"""

    metamodel: Metamodel = Field(..., description="Complete metamodel object")
    nodes: list[dict[str, Any]] = Field(
        default_factory=list, description="List of all nodes (concepts, attributes, relationships)"
    )
    edges: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of all edges (domain, range, has_attribute, subclass_of)",
    )
    edgeConstraints: list[EdgeType] = Field(
        default_factory=list, description="Edge type constraints from M3 configuration"
    )

    class Config:
        from_attributes = True
