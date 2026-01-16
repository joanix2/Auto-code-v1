"""
Relationship Model - Associations between concepts
Stored as relationships in Neo4j graph
"""
from pydantic import BaseModel, Field, computed_field
from typing import Optional
from enum import Enum

from ..graph import Edge



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


class Relationship(Edge):
    """
    Relationship - Association between two concepts (an edge in the graph)
    Stored as a relationship in Neo4j between concept nodes
    
    Inherits from Edge:
    - description (from Edge)
    - source_id, target_id (connected nodes)
    - source_label, target_label (cached labels)
    - graph_id (parent metamodel)
    
    The name is computed based on:
    - IS_A: "is_a {target_concept_name}"
    - HAS_SUBCLASS: "has_subclass {target_concept_name}" (inverse of is_a)
    - HAS_PART: "has_part {target_concept_name}"
    - PART_OF: "part_of {target_concept_name}" (inverse of has_part)
    """
    type: RelationshipType = Field(..., description="Type of relationship")
    
    # Backward compatibility - map to Edge properties
    @property
    def source_concept_id(self) -> str:
        """Alias for source_id (backward compatibility)"""
        return self.source_id
    
    @source_concept_id.setter
    def source_concept_id(self, value: str):
        """Setter for source_concept_id (backward compatibility)"""
        self.source_id = value
    
    @property
    def target_concept_id(self) -> str:
        """Alias for target_id (backward compatibility)"""
        return self.target_id
    
    @target_concept_id.setter
    def target_concept_id(self, value: str):
        """Setter for target_concept_id (backward compatibility)"""
        self.target_id = value
    
    @property
    def target_concept_name(self) -> Optional[str]:
        """Alias for target_label (backward compatibility)"""
        return self.target_label
    
    @target_concept_name.setter
    def target_concept_name(self, value: Optional[str]):
        """Setter for target_concept_name (backward compatibility)"""
        self.target_label = value
    
    @property
    def metamodel_id(self) -> str:
        """Alias for graph_id (backward compatibility)"""
        return self.graph_id
    
    @metamodel_id.setter
    def metamodel_id(self, value: str):
        """Setter for metamodel_id (backward compatibility)"""
        self.graph_id = value
    
    # Abstract methods implementation
    def get_edge_type(self) -> str:
        """Return the relationship type as string"""
        return self.type.value
    
    def get_display_label(self) -> str:
        """Return the relationship type as display label"""
        if self.target_label:
            return f"{self.type.value} {self.target_label}"
        return self.type.value
    
    def is_directed(self) -> bool:
        """All relationships are directed"""
        return True
    
    @computed_field
    @property
    def name(self) -> str:
        """
        Compute relationship name based on type and target concept.
        For OTHER type, uses the stored name from Edge.name field.
        """
        # For custom relationships (OTHER), use the stored name from the Edge parent class
        if self.type == RelationshipType.OTHER:
            # Access the actual field value from Edge
            stored_name = self.__dict__.get('name')
            return stored_name if stored_name else "other"
        
        # For standard relationships, compute the name
        if not self.target_label:
            return self.type.value
        
        if self.type == RelationshipType.IS_A:
            return f"is_a_{self.target_label}"
        elif self.type == RelationshipType.HAS_SUBCLASS:
            return f"has_subclass_{self.target_label}"
        elif self.type == RelationshipType.HAS_PART:
            return f"has_part_{self.target_label}"
        elif self.type == RelationshipType.PART_OF:
            return f"part_of_{self.target_label}"
        else:
            return self.type.value
    
    class Config:
        from_attributes = True


# API Schemas

class RelationshipCreate(BaseModel):
    """Schema for creating a relationship"""
    type: RelationshipType
    source_concept_id: str
    target_concept_id: str
    target_concept_name: Optional[str] = None  # Will be fetched from target concept if not provided
    description: Optional[str] = None
    metamodel_id: str


class RelationshipUpdate(BaseModel):
    """Schema for updating a relationship"""
    type: Optional[RelationshipType] = None
    target_concept_name: Optional[str] = None
    description: Optional[str] = None


class RelationshipResponse(Relationship):
    """Schema for relationship response"""
    pass

