"""
MDE (Model-Driven Engineering) models
"""
from .M2.metamodel import Metamodel, MetamodelCreate, MetamodelUpdate, MetamodelResponse, MetamodelWithDetails, MetamodelGraphResponse, MetamodelStatus
from .M2.concept import Concept, ConceptCreate, ConceptUpdate, ConceptResponse
from .M2.attribute import Attribute, AttributeCreate, AttributeUpdate, AttributeResponse, AttributeType
from .M2.relationship import Relationship, RelationshipCreate, RelationshipUpdate, RelationshipResponse, RelationshipType
from .M2.metamodel_edge import MetamodelEdge, MetamodelEdgeType, MetamodelEdgeCreate, MetamodelEdgeUpdate, MetamodelEdgeResponse

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
