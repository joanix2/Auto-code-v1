"""
M3 Configuration - Meta-dsl type definitions

This defines the concrete types available in the dsl layer.
This is the single source of truth for node and edge types.
"""

from ..base import GenderType
from ..abstract.edge_type import AbstractEdgeType
from ..abstract.node_type import AbstractNodeType

# ==================== NODE TYPES ====================

CONCEPT_NODE_TYPE = AbstractNodeType(
    name="concept",
    description="Représente une classe ou entité du domaine",
    label="Concept",
    labelPlural="Concepts",
    gender=GenderType.MASCULIN,
    article="le",
)

ATTRIBUTE_NODE_TYPE = AbstractNodeType(
    name="attribute",
    description="Représente une propriété ou caractéristique",
    label="Attribut",
    labelPlural="Attributs",
    gender=GenderType.MASCULIN,
    article="l'",
)

RELATION_NODE_TYPE = AbstractNodeType(
    name="relation",
    description="Représente une association entre concepts",
    label="Relation",
    labelPlural="Relations",
    gender=GenderType.FEMININ,
    article="la",
)


# Node types registry
NODE_TYPES: list[AbstractNodeType] = [
    CONCEPT_NODE_TYPE,
    ATTRIBUTE_NODE_TYPE,
    RELATION_NODE_TYPE,
]

NODE_TYPES_BY_ID: dict[str, AbstractNodeType] = {nt.name: nt for nt in NODE_TYPES}


# ==================== EDGE TYPES ====================

DOMAIN_EDGE_TYPE = AbstractEdgeType(
    name="domain",
    description="Définit le concept de domaine d'une relation",
    sourceNodeTypes=["relation"],
    targetNodeTypes=["concept"],
    directed=True,
)

RANGE_EDGE_TYPE = AbstractEdgeType(
    name="range",
    description="Définit le concept de co-domaine (range) d'une relation",
    sourceNodeTypes=["relation"],
    targetNodeTypes=["concept"],
    directed=True,
)

HAS_ATTRIBUTE_EDGE_TYPE = AbstractEdgeType(
    name="has_attribute",
    description="Associe un attribut à un concept",
    sourceNodeTypes=["concept"],
    targetNodeTypes=["attribute"],
    directed=True,
)

SUBCLASS_OF_EDGE_TYPE = AbstractEdgeType(
    name="subclass_of",
    description="Définit une relation d'héritage entre concepts",
    sourceNodeTypes=["concept"],
    targetNodeTypes=["concept"],
    directed=True,
)


# Edge types registry
EDGE_TYPES: list[AbstractEdgeType] = [
    DOMAIN_EDGE_TYPE,
    RANGE_EDGE_TYPE,
    HAS_ATTRIBUTE_EDGE_TYPE,
    SUBCLASS_OF_EDGE_TYPE,
]

EDGE_TYPES_BY_ID: dict[str, AbstractEdgeType] = {et.name: et for et in EDGE_TYPES}


# ==================== M3 CONFIGURATION ====================


class DSLConfig:
    """
    M3 Configuration class providing access to all dsl types
    """

    @staticmethod
    def get_node_types() -> list[AbstractNodeType]:
        """Get all available node types"""
        return NODE_TYPES

    @staticmethod
    def get_node_type(type_id: str) -> AbstractNodeType | None:
        """Get a specific node type by ID"""
        return NODE_TYPES_BY_ID.get(type_id)

    @staticmethod
    def get_edge_types() -> list[AbstractEdgeType]:
        """Get all available edge types"""
        return EDGE_TYPES

    @staticmethod
    def get_edge_type(type_id: str) -> AbstractEdgeType | None:
        """Get a specific edge type by ID"""
        return EDGE_TYPES_BY_ID.get(type_id)

    @staticmethod
    def get_edge_constraints() -> list[dict]:
        """
        Get edge constraints for the graph editor

        Returns constraints in the format expected by the frontend:
        {
            "edgeType": "DOMAIN",
            "label": "DOMAIN",
            "sourceNodeType": "relation",
            "targetNodeType": "concept",
            "directed": true
        }
        """
        constraints = []
        for edge_type in EDGE_TYPES:
            for source_type in edge_type.sourceNodeTypes:
                for target_type in edge_type.targetNodeTypes:
                    constraints.append(
                        {
                            "edgeType": edge_type.name.upper(),  # Uppercase for display
                            "label": edge_type.name.upper(),
                            "sourceNodeType": source_type,
                            "targetNodeType": target_type,
                            "directed": edge_type.directed,
                        }
                    )
        return constraints

    @staticmethod
    def validate_edge(edge_type_id: str, source_type_id: str, target_type_id: str) -> bool:
        """
        Validate if an edge connection is allowed

        Args:
            edge_type_id: ID of the edge type (lowercase)
            source_type_id: ID of the source node type
            target_type_id: ID of the target node type

        Returns:
            True if the connection is valid, False otherwise
        """
        edge_type = EDGE_TYPES_BY_ID.get(edge_type_id)
        if not edge_type:
            return False

        return edge_type.allows_connection(source_type_id, target_type_id)
