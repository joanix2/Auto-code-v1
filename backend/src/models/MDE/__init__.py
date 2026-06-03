"""
MDE (Model-Driven Engineering) models
"""

from .M2.attribute import (
    Attribute,
    AttributeCreate,
    AttributeResponse,
    AttributeType,
    AttributeUpdate,
)
from .M2.concept import Concept, ConceptCreate, ConceptResponse, ConceptUpdate
from .M2.metamodel import (
    Metamodel,
    MetamodelCreate,
    MetamodelGraphResponse,
    MetamodelResponse,
    MetamodelStatus,
    MetamodelUpdate,
    MetamodelWithDetails,
)
from .M2.metamodel_edge import (
    MetamodelEdge,
    MetamodelEdgeCreate,
    MetamodelEdgeResponse,
    MetamodelEdgeType,
    MetamodelEdgeUpdate,
)
from .M2.relationship import (
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
    "AttributeType",
    # Relationship
    "Relationship",
    "RelationshipCreate",
    "RelationshipUpdate",
    "RelationshipResponse",
    "RelationshipType",
    # MetamodelEdge
    "MetamodelEdge",
    "MetamodelEdgeType",
    "MetamodelEdgeCreate",
    "MetamodelEdgeUpdate",
    "MetamodelEdgeResponse",
]
