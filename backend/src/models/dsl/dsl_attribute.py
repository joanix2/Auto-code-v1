"""
Attribute Model - Properties of concepts
Stored as separate nodes in Neo4j linked to concepts
"""

from enum import Enum

from pydantic import BaseModel, Field

from ..abstract import AbstractNode


class AttributeType(str, Enum):
    """Types for attributes"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"


class DSLAttribute(AbstractNode):
    """
    Attribute - Property/field of a concept (a node in the graph)
    Stored as a node in Neo4j with relationship to its concept

    Inherits from Node:
    - name, description (from Node)
    - x_position, y_position (for graph visualization)
    - graph_id (parent dsl)
    """

    type: AttributeType = Field(..., description="Attribute type")

    # Constraints
    is_required: bool = Field(default=False, description="Is the attribute required")
    is_unique: bool = Field(default=False, description="Must the value be unique")

    # Parent concept - will be a relationship in Neo4j (optional for standalone attributes)
    concept_id: str | None = Field(default=None, description="Parent concept ID")

    # Abstract methods implementation
    def get_node_type(self) -> str:
        """Return 'attribute' as the node type"""
        return "attribute"

    def get_display_label(self) -> str:
        """Return the attribute name as display label"""
        return self.name

    def to_graph_dict(self):
        """
        Override to include attribute-specific properties
        """
        base_dict = super().to_graph_dict()
        base_dict.update(
            {
                "dataType": self.type.value,  # Type de données (string, integer, etc.)
                "isRequired": self.is_required,  # Attribut requis
                "isUnique": self.is_unique,  # Valeur unique
                "concept_id": self.concept_id,  # ID du concept parent (optionnel)
            }
        )
        return base_dict

    class Config:
        from_attributes = True


# API Schemas


class DSLAttributeCreate(BaseModel):
    """Schema for creating an attribute"""

    name: str = Field(..., min_length=1)
    type: AttributeType
    description: str | None = None
    is_required: bool = False
    is_unique: bool = False
    concept_id: str | None = None  # Optional - can be linked to concept later
    graph_id: str  # Required - must belong to a dsl


class DSLAttributeUpdate(BaseModel):
    """Schema for updating an attribute"""

    name: str | None = None
    type: AttributeType | None = None
    description: str | None = None
    is_required: bool | None = None
    is_unique: bool | None = None


class DSLAttributeResponse(DSLAttribute):
    """Schema for attribute response"""

    pass
