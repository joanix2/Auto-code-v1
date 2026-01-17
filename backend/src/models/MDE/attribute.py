"""
Attribute Model - Properties of concepts
Stored as separate nodes in Neo4j linked to concepts
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

from ..graph import Node



class AttributeType(str, Enum):
    """Types for attributes"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"

class Attribute(Node):
    """
    Attribute - Property/field of a concept (a node in the graph)
    Stored as a node in Neo4j with relationship to its concept
    
    Inherits from Node:
    - name, description (from Node)
    - x_position, y_position (for graph visualization)
    - graph_id (parent metamodel)
    """
    type: AttributeType = Field(..., description="Attribute type")
    
    # Constraints
    is_required: bool = Field(default=False, description="Is the attribute required")
    is_unique: bool = Field(default=False, description="Must the value be unique")
    
    # Parent concept - will be a relationship in Neo4j (optional for standalone attributes)
    concept_id: Optional[str] = Field(default=None, description="Parent concept ID")
    
    # Abstract methods implementation
    def get_node_type(self) -> str:
        """Return 'attribute' as the node type"""
        return "attribute"
    
    def get_display_label(self) -> str:
        """Return the attribute name and type as display label"""
        return f"{self.name}: {self.type.value}"
    
    class Config:
        from_attributes = True


# API Schemas

class AttributeCreate(BaseModel):
    """Schema for creating an attribute"""
    name: str = Field(..., min_length=1)
    type: AttributeType
    description: Optional[str] = None
    is_required: bool = False
    is_unique: bool = False
    concept_id: Optional[str] = None  # Optional - can be linked to concept later
    graph_id: str  # Required - must belong to a metamodel


class AttributeUpdate(BaseModel):
    """Schema for updating an attribute"""
    name: Optional[str] = None
    type: Optional[AttributeType] = None
    description: Optional[str] = None
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None


class AttributeResponse(Attribute):
    """Schema for attribute response"""
    pass
