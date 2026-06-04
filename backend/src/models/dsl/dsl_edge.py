"""
MetamodelEdge - Edges in the metamodel graph (domain, range, has_attribute, etc.)
"""

from enum import Enum

from pydantic import BaseModel, Field

from ..abstract.edge import AbstractEdge


class DSLEdgeType(str, Enum):
    """Types of edges in a metamodel"""

    DOMAIN = "domain"  # Relation → Source Concept
    RANGE = "range"  # Relation → Target Concept
    HAS_ATTRIBUTE = "has_attribute"  # Concept → Attribute
    SUBCLASS_OF = "subclass_of"  # Concept → Concept (inheritance)

    def get_display_label(self) -> str:
        """Return the label in UPPERCASE for display (Neo4j convention)"""
        return self.value.upper()

    def get_description(self) -> str:
        """Return human-readable description of this edge type"""
        descriptions = {
            "domain": "Définit le concept de domaine d'une relation (source)",
            "range": "Définit le concept de portée d'une relation (cible)",
            "has_attribute": "Relie un concept à un de ses attributs",
            "subclass_of": "Définit une relation d'héritage entre concepts",
        }
        return descriptions.get(self.value, "")


class DSLEdge(AbstractEdge):
    """
    MetamodelEdge - Represents connections in the metamodel graph

    Types d'edges:
    - DOMAIN: Relie une Relation à son Concept source
    - RANGE: Relie une Relation à son Concept cible
    - HAS_ATTRIBUTE: Relie un Concept à un Attribut
    - SUBCLASS_OF: Relie un Concept enfant à un Concept parent (héritage)

    Structure Neo4j:
    (Relation)-[:DOMAIN]->(Concept)
    (Relation)-[:RANGE]->(Concept)
    (Concept)-[:HAS_ATTRIBUTE]->(Attribute)
    (Concept)-[:SUBCLASS_OF]->(Concept)
    """

    edge_type: DSLEdgeType = Field(..., description="Type of metamodel edge")

    def get_edge_type(self) -> str:
        """Return the edge type"""
        return self.edge_type.value

    def get_display_label(self) -> str:
        """Return the label to display on the edge in UPPERCASE like Neo4j"""
        return self.edge_type.get_display_label()

    def is_directed(self) -> bool:
        """All metamodel edges are directed"""
        return True

    class Config:
        from_attributes = True


class DSLEdgeCreate(BaseModel):
    """Schema for creating a metamodel edge"""

    edge_type: DSLEdgeType = Field(..., description="Type of metamodel edge")
    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    graph_id: str = Field(..., description="ID of the metamodel")
    description: str | None = None


class DSLEdgeUpdate(BaseModel):
    """Schema for updating a metamodel edge"""

    description: str | None = None


class DSLEdgeResponse(DSLEdge):
    """Schema for metamodel edge response"""

    pass
