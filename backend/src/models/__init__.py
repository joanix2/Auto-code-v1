"""
Pydantic models for all entities
"""

from .base import BaseEntity, TimestampMixin
from .abstract import AbstractGraph, AbstractNode, AbstractEdge, AbstractNodeType, AbstractEdgeType
from .dsl import (
    DSLGraph,
    DSLGraphCreate,
    DSLGraphResponse,
    DSLGraphUpdate,
    DSLGraphWithDetails,

    DSLConcept,
    DSLConceptCreate,
    DSLConceptResponse,
    DSLConceptUpdate,
    DSLAttribute,
    DSLAttributeCreate,
    DSLAttributeResponse,
    DSLAttributeUpdate,
    AttributeType,
    DSLRelation,
    DSLRelationCreate,
    DSLRelationResponse,
    DSLRelationUpdate,
    DSLRelationType,
    DSLEdge,
    DSLEdgeCreate,
    DSLEdgeResponse,
    DSLEdgeType,
    DSLEdgeUpdate,
    DSLConfig,
)
from .MDE import (
    Attribute,
    AttributeCreate,
    AttributeResponse,
    AttributeType,
    AttributeUpdate,
    Concept,
    ConceptCreate,
    ConceptResponse,
    ConceptUpdate,
    Metamodel,
    MetamodelCreate,
    MetamodelEdge,
    MetamodelEdgeCreate,
    MetamodelEdgeResponse,
    MetamodelEdgeType,
    MetamodelEdgeUpdate,
    MetamodelGraphResponse,
    MetamodelResponse,
    MetamodelStatus,
    MetamodelUpdate,
    Relationship,
    RelationshipCreate,
    RelationshipResponse,
    RelationshipType,
    RelationshipUpdate,
)
from .oauth.user import User, UserCreate, UserPublic, UserUpdate
from .repository.issue import Issue, IssueCreate, IssuePriority, IssueStatus, IssueType, IssueUpdate
from .repository.message import Message, MessageAuthorType, MessageCreate, MessageUpdate
from .repository.repository import Repository, RepositoryCreate, RepositoryUpdate

__all__ = [
    # Base
    "BaseEntity",
    "TimestampMixin",
    # Abstract
    "AbstractGraph",
    "AbstractNode",
    "AbstractEdge",
    "AbstractNodeType",
    "AbstractEdgeType",
    # DSL
    "DSLGraph",
    "DSLGraphCreate",
    "DSLGraphUpdate",
    "DSLGraphResponse",
    "DSLGraphWithDetails",

    "DSLConcept",
    "DSLConceptCreate",
    "DSLConceptUpdate",
    "DSLConceptResponse",
    "DSLAttribute",
    "DSLAttributeCreate",
    "DSLAttributeUpdate",
    "DSLAttributeResponse",
    "DSLRelation",
    "DSLRelationCreate",
    "DSLRelationUpdate",
    "DSLRelationResponse",
    "DSLRelationType",
    "DSLEdge",
    "DSLEdgeCreate",
    "DSLEdgeUpdate",
    "DSLEdgeResponse",
    "DSLEdgeType",
    "DSLConfig",
    "AttributeType",
    # User
    "User",
    "UserCreate",
    "UserUpdate",
    "UserPublic",
    # Repository
    "Repository",
    "RepositoryCreate",
    "RepositoryUpdate",
    # Issue
    "Issue",
    "IssueCreate",
    "IssueUpdate",
    "IssueStatus",
    "IssuePriority",
    "IssueType",
    # Message
    "Message",
    "MessageCreate",
    "MessageUpdate",
    "MessageAuthorType",
    # Metamodel
    "Metamodel",
    "MetamodelCreate",
    "MetamodelUpdate",
    "MetamodelResponse",
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
]
