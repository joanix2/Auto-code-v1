"""
Relationship Model - Associations between concepts (Object Properties in ontology)
Stored as nodes in Neo4j graph with DOMAIN and RANGE edges
"""

from enum import Enum

from pydantic import BaseModel, Field

from ..abstract import AbstractNode


class DSLRelationType(str, Enum):
    """Types of relationships between concepts"""

    # Direct relationships
    IS_A = "is_a"  # inheritance - A is_a B
    HAS_PART = "has_part"  # composition - A has_part B

    # Inverse relationships (automatically created)
    HAS_SUBCLASS = "has_subclass"  # inverse of is_a - B has_subclass A
    PART_OF = "part_of"  # inverse of has_part - B part_of A

    # Custom relationship
    OTHER = "other"  # custom relationship with user-defined name


class DSLRelation(AbstractNode):
    """
    Relationship - Object Property node in ontology
    Stored as a node in Neo4j with DOMAIN and RANGE edges to concepts

    Structure:
    (DSL)-[:HAS_RELATION]->(Relationship)
    (Relationship)-[:DOMAIN]->(SourceConcept)
    (Relationship)-[:RANGE]->(TargetConcept)

    Inherits from Node:
    - id, name, description
    - x_position, y_position
    - graph_id (parent dsl)
    - created_at, updated_at
    """

    type: DSLRelationType = Field(..., description="Type of relationship")

    # Abstract methods implementation
    def get_node_type(self) -> str:
        """Return 'relation' as node type"""
        return "relation"

    def get_display_label(self) -> str:
        """Return the relationship name as display label"""
        return self.name

    def to_graph_dict(self):
        """
        Override to include relationship-specific properties
        """
        base_dict = super().to_graph_dict()
        base_dict.update(
            {
                "relationType": self.type.value,  # Type de relation (is_a, has_part, etc.)
            }
        )
        return base_dict

    class Config:
        from_attributes = True


# API Schemas


class DSLRelationCreate(BaseModel):
    """Schema for creating a relationship

    Les connexions aux concepts se font via les edges DOMAIN/RANGE dans le graphe Neo4j
    """

    name: str = Field(
        ..., min_length=1, description="Relationship name (e.g., 'has_parent', 'belongs_to')"
    )
    type: DSLRelationType
    description: str | None = None
    graph_id: str  # ID du dsl parent
    x_position: float | None = None
    y_position: float | None = None


class DSLRelationUpdate(BaseModel):
    """Schema for updating a relationship"""

    name: str | None = Field(None, min_length=1, description="Relationship name")
    type: DSLRelationType | None = None
    description: str | None = None
    x_position: float | None = None
    y_position: float | None = None


class DSLRelationResponse(DSLRelation):
    """Schema for relationship response"""

    pass
