"""
Concept Model - Represents classes in the metamodel (MDE)
Simplified for Neo4j graph database
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from ...graph import Node


class Concept(Node):
    """
    Concept - Represents a class/entity in the metamodel (a node in the graph)
    Stored as a node in Neo4j with relationships to attributes
    
    Inherits from Node:
    - name, description (from Node)
    - x_position, y_position (for graph visualization)
    - graph_id (parent metamodel)
    """
    
    # Abstract methods implementation
    def get_node_type(self) -> str:
        """Return 'concept' as the node type"""
        return "concept"
    
    def get_display_label(self) -> str:
        """Return the concept name as display label"""
        return self.name
    
    class Config:
        from_attributes = True


# API Schemas

class ConceptCreate(BaseModel):
    """Schema for creating a concept"""
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    graph_id: str
    x_position: Optional[float] = None
    y_position: Optional[float] = None


class ConceptUpdate(BaseModel):
    """Schema for updating a concept"""
    name: Optional[str] = None
    description: Optional[str] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None


class ConceptResponse(Concept):
    """Schema for concept response"""
    pass
