"""
Relationship Model - Associations between concepts (Object Properties in ontology)
Stored as nodes in Neo4j graph with DOMAIN and RANGE edges
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum

from ...graph import Node


class RelationshipType(str, Enum):
    """Types of relationships between concepts"""
    # Direct relationships
    IS_A = "is_a"  # inheritance - A is_a B
    HAS_PART = "has_part"  # composition - A has_part B
    
    # Inverse relationships (automatically created)
    HAS_SUBCLASS = "has_subclass"  # inverse of is_a - B has_subclass A
    PART_OF = "part_of"  # inverse of has_part - B part_of A
    
    # Custom relationship
    OTHER = "other"  # custom relationship with user-defined name


class Relationship(Node):
    """
    Relationship - Object Property node in ontology
    Stored as a node in Neo4j with DOMAIN and RANGE edges to concepts
    
    Structure:
    (Metamodel)-[:HAS_RELATION]->(Relationship)
    (Relationship)-[:DOMAIN]->(SourceConcept)
    (Relationship)-[:RANGE]->(TargetConcept)
    
    Inherits from Node:
    - id, name, description
    - x_position, y_position
    - graph_id (parent metamodel)
    - created_at, updated_at
    """
    type: RelationshipType = Field(..., description="Type of relationship")
    
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
        base_dict.update({
            "relationType": self.type.value,  # Type de relation (is_a, has_part, etc.)
        })
        return base_dict
    
    class Config:
        from_attributes = True


# API Schemas

class RelationshipCreate(BaseModel):
    """Schema for creating a relationship
    
    Les connexions aux concepts se font via les edges DOMAIN/RANGE dans le graphe Neo4j
    """
    name: str = Field(..., min_length=1, description="Relationship name (e.g., 'has_parent', 'belongs_to')")
    type: RelationshipType
    description: Optional[str] = None
    graph_id: str  # ID du metamodel parent
    x_position: Optional[float] = None
    y_position: Optional[float] = None


class RelationshipUpdate(BaseModel):
    """Schema for updating a relationship"""
    name: Optional[str] = Field(None, min_length=1, description="Relationship name")
    type: Optional[RelationshipType] = None
    description: Optional[str] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None


class RelationshipResponse(Relationship):
    """Schema for relationship response"""
    pass


