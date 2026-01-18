"""
MetamodelEdge - Edges in the metamodel graph (domain, range, has_attribute, etc.)
"""
from enum import Enum
from pydantic import Field
from typing import Optional

from ...graph.edge import Edge


class MetamodelEdgeType(str, Enum):
    """Types of edges in a metamodel"""
    DOMAIN = "domain"           # Relation → Source Concept
    RANGE = "range"             # Relation → Target Concept
    HAS_ATTRIBUTE = "has_attribute"  # Concept → Attribute
    SUBCLASS_OF = "subclass_of"      # Concept → Concept (inheritance)


class MetamodelEdge(Edge):
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
    
    edge_type: MetamodelEdgeType = Field(..., description="Type of metamodel edge")
    
    def get_edge_type(self) -> str:
        """Return the edge type"""
        return self.edge_type.value
    
    def get_display_label(self) -> str:
        """Return the label to display on the edge"""
        labels = {
            MetamodelEdgeType.DOMAIN: "domain",
            MetamodelEdgeType.RANGE: "range",
            MetamodelEdgeType.HAS_ATTRIBUTE: "has",
            MetamodelEdgeType.SUBCLASS_OF: "subclass of",
        }
        return labels.get(self.edge_type, self.edge_type.value)
    
    def is_directed(self) -> bool:
        """All metamodel edges are directed"""
        return True
    
    class Config:
        from_attributes = True


class MetamodelEdgeCreate(Edge):
    """Schema for creating a metamodel edge"""
    edge_type: MetamodelEdgeType = Field(..., description="Type of metamodel edge")
    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    graph_id: str = Field(..., description="ID of the metamodel")
    description: Optional[str] = None


class MetamodelEdgeUpdate(Edge):
    """Schema for updating a metamodel edge"""
    description: Optional[str] = None


class MetamodelEdgeResponse(MetamodelEdge):
    """Schema for metamodel edge response"""
    pass
