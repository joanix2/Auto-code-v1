"""
MDE (Model-Driven Engineering) models
"""
from .metamodel import Metamodel, MetamodelCreate, MetamodelUpdate, MetamodelResponse, MetamodelWithDetails, MetamodelStatus
from .concept import Concept, ConceptCreate, ConceptUpdate, ConceptResponse
from .attribute import Attribute, AttributeCreate, AttributeUpdate, AttributeResponse, AttributeType
from .relationship import Relationship, RelationshipCreate, RelationshipUpdate, RelationshipResponse, RelationshipType

__all__ = [
    # Metamodel
    "Metamodel",
    "MetamodelCreate",
    "MetamodelUpdate",
    "MetamodelResponse",
    "MetamodelWithDetails",
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
]
