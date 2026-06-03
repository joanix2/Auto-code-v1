"""
Metamodel package - Contains all metamodel-related models
"""

from .attribute import Attribute, AttributeCreate, AttributeResponse, AttributeUpdate
from .concept import Concept, ConceptCreate, ConceptResponse, ConceptUpdate
from .metamodel import (
    Metamodel,
    MetamodelCreate,
    MetamodelGraphResponse,
    MetamodelResponse,
    MetamodelStatus,
    MetamodelUpdate,
    MetamodelWithDetails,
)
from .metamodel_edge import (
    MetamodelEdge,
    MetamodelEdgeCreate,
    MetamodelEdgeResponse,
    MetamodelEdgeType,
    MetamodelEdgeUpdate,
)
from .relationship import (
    Relationship,
    RelationshipCreate,
    RelationshipResponse,
    RelationshipType,
    RelationshipUpdate,
)

__all__ = [
    # Metamodel
    "Metamodel",
    "MetamodelCreate",
    "MetamodelUpdate",
    "MetamodelResponse",
    "MetamodelWithDetails",
    "MetamodelGraphResponse",
    "MetamodelStatus",
    # Concept
    "Concept",
    "ConceptCreate",
    "ConceptUpdate",
    "ConceptResponse",
    # Attribute
    "Attribute",
    "AttributeCreate",
    "AttributeUpdate",
    "AttributeResponse",
    # Relationship
    "Relationship",
    "RelationshipType",
    "RelationshipCreate",
    "RelationshipUpdate",
    "RelationshipResponse",
    # Edge
    "MetamodelEdge",
    "MetamodelEdgeType",
    "MetamodelEdgeCreate",
    "MetamodelEdgeUpdate",
    "MetamodelEdgeResponse",
]
