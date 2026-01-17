"""
Relationship Model - Associations between concepts (Object Properties in ontology)
Stored as nodes in Neo4j graph with DOMAIN and RANGE edges
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

from ..graph import Node


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
    
    # Cached IDs and labels from DOMAIN/RANGE edges (for convenience)
    source_concept_id: Optional[str] = Field(default=None, description="Source concept ID (from DOMAIN edge)")
    target_concept_id: Optional[str] = Field(default=None, description="Target concept ID (from RANGE edge)")
    source_label: Optional[str] = Field(default=None, description="Source concept name (cached)")
    target_label: Optional[str] = Field(default=None, description="Target concept name (cached)")
    
    # Backward compatibility aliases
    @property
    def source_id(self) -> Optional[str]:
        """Alias for source_concept_id"""
        return self.source_concept_id
    
    @property
    def target_id(self) -> Optional[str]:
        """Alias for target_concept_id"""
        return self.target_concept_id
    
    @property
    def target_concept_name(self) -> Optional[str]:
        """Alias for target_label"""
        return self.target_label
    
    @property
    def metamodel_id(self) -> str:
        """Alias for graph_id"""
        return self.graph_id
    
    # Abstract methods implementation
    def get_node_type(self) -> str:
        """Return 'relation' as node type"""
        return "relation"
    
    def get_display_label(self) -> str:
        """Return the relationship name as display label"""
        return self.name
    
    class Config:
        from_attributes = True


# API Schemas

class RelationshipCreate(BaseModel):
    """Schema for creating a relationship"""
    name: str = Field(..., min_length=1, description="Relationship name (e.g., 'has_parent', 'belongs_to')")
    type: RelationshipType
    source_concept_id: str
    target_concept_id: str
    description: Optional[str] = None
    metamodel_id: str
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


