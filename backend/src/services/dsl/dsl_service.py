import logging
from typing import Any

from src.models.dsl import DSLGraph

from ...repositories.dsl.dsl_attribute_repository import DSLAttributeRepository
from ...repositories.dsl.dsl_concept_repository import DSLConceptRepository
from ...repositories.dsl.dsl_edge_repository import DSLEdgeRepository
from ...repositories.dsl.dsl_repository import DSLRepository
from ...repositories.dsl.dsl_relation_repository import DSLRelationRepository
from ..base_service import BaseService

logger = logging.getLogger(__name__)


class DSLService(BaseService[DSLGraph]):
    def __init__(
        self,
        repository: DSLRepository,
        dsl_concept_repository: DSLConceptRepository | None = None,
        dsl_attribute_repository: DSLAttributeRepository | None = None,
        relationship_repository: DSLRelationRepository | None = None,
        dsl_edge_repository: DSLEdgeRepository | None = None,
    ):
        """
        Initialize dsl service

        Args:
            repository: DSLRepository instance
            dsl_concept_repository: DSLConceptRepository instance (optional)
            dsl_attribute_repository: DSLAttributeRepository instance (optional)
            relationship_repository: DSLRelationRepository instance (optional)
            dsl_edge_repository: DSLEdgeRepository instance (optional)
        """
        self.repository = repository
        self.dsl_concept_repository = dsl_concept_repository
        self.dsl_attribute_repository = dsl_attribute_repository
        self.relationship_repository = relationship_repository
        self.dsl_edge_repository = dsl_edge_repository

    # Implementation of BaseService interface

    async def create(self, data: dict[str, Any]) -> DSLGraph:
        """Create a new dsl"""
        logger.info(f"🚀 Service: Creating dsl: {data.get('name')}")
        return await self.repository.create(data)

    async def get_by_id(self, entity_id: str) -> DSLGraph | None:
        """Get dsl by ID"""
        logger.info(f"🔍 Service: Getting dsl by ID: {entity_id}")
        return await self.repository.get_by_id(entity_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[DSLGraph]:
        """Get all dsls with optional pagination"""
        logger.info(f"🔍 Service: Getting all dsls (skip={skip}, limit={limit})")
        return await self.repository.get_all(skip, limit)

    async def update(self, entity_id: str, update_data: dict[str, Any]) -> DSLGraph | None:
        """Update dsl"""
        logger.info(f"✏️ Service: Updating dsl: {entity_id}")
        return await self.repository.update(entity_id, update_data)

    async def delete(self, entity_id: str) -> bool:
        """Delete dsl"""
        logger.info(f"🗑️ Service: Deleting dsl: {entity_id}")
        return await self.repository.delete(entity_id)

    # Custom methods

    async def get_by_name(self, name: str) -> DSLGraph | None:
        """Get a dsl by name"""
        logger.info(f"🔍 Service: Getting dsl by name: {name}")
        return await self.repository.get_by_name(name)

    async def get_by_status(self, status: str) -> list[DSLGraph]:
        """Get all dsls with a specific status"""
        logger.info(f"🔍 Service: Getting dsls with status: {status}")
        return await self.repository.get_by_status(status)

    async def get_by_author(self, author: str) -> list[DSLGraph]:
        """Get all dsls by author"""
        logger.info(f"🔍 Service: Getting dsls by author: {author}")
        return await self.repository.get_by_author(author)

    async def validate_dsl(self, dsl_id: str) -> DSLGraph:
        """Change dsl status to validated"""
        logger.info(f"✅ Service: Validating dsl: {dsl_id}")
        return await self.update(dsl_id, {"status": "validated"})

    async def deprecate_dsl(self, dsl_id: str) -> DSLGraph:
        """Change dsl status to deprecated"""
        logger.info(f"⚠️ Service: Deprecating dsl: {dsl_id}")
        return await self.update(dsl_id, {"status": "deprecated"})

    async def get_dsl_with_graph(self, dsl_id: str) -> dict[str, Any]:
        """
        Get a complete dsl with all its nodes and edges as a graph structure

        Returns a dictionary containing:
        - dsl: The complete DSLGraph object (not a dict)
        - nodes: List of all nodes with their graph representation
        - edges: List of all edges with their graph representation

        Args:
            dsl_id: ID of the dsl

        Returns:
            Dict with keys: dsl, nodes, edges
        """
        logger.info(f"📊 Service: Getting complete dsl graph: {dsl_id}")

        # Récupérer le dsl
        dsl = await self.get_by_id(dsl_id)
        if not dsl:
            raise ValueError(f"DSLGraph {dsl_id} not found")

        nodes = []
        edges = []

        # Récupérer les DSLConcepts
        if self.dsl_concept_repository:
            concepts = await self.dsl_concept_repository.get_by_dsl(dsl_id)
            nodes.extend([c.to_graph_dict() for c in concepts])
            logger.info(f"  ✓ Found {len(concepts)} concepts")

        # Récupérer TOUS les Attributs (standalone ET attachés à des concepts)
        if self.dsl_attribute_repository:
            attributes = await self.dsl_attribute_repository.get_by_dsl(dsl_id)
            nodes.extend([a.to_graph_dict() for a in attributes])
            logger.info(f"  ✓ Found {len(attributes)} attributes (standalone and attached)")

        # Récupérer les Relations
        if self.relationship_repository:
            relationships = await self.relationship_repository.get_by_dsl(dsl_id)
            nodes.extend([r.to_graph_dict() for r in relationships])
            logger.info(f"  ✓ Found {len(relationships)} relationships")

        # Créer un Set des IDs de nœuds existants
        node_ids = {node["id"] for node in nodes}
        logger.info(f"  📋 Total node IDs: {len(node_ids)}")

        # Récupérer les Edges
        if self.dsl_edge_repository:
            dsl_edges = await self.dsl_edge_repository.get_by_dsl(dsl_id)

            # Filtrer les edges orphelins (qui pointent vers des nœuds inexistants)
            valid_edges = []
            orphaned_edges = []

            for edge in dsl_edges:
                edge_dict = edge.to_graph_dict()
                has_valid_source = edge_dict["source"] in node_ids
                has_valid_target = edge_dict["target"] in node_ids

                if has_valid_source and has_valid_target:
                    valid_edges.append(edge_dict)
                else:
                    orphaned_edges.append(
                        {
                            "id": edge_dict["id"],
                            "source": edge_dict["source"],
                            "target": edge_dict["target"],
                            "type": edge_dict["type"],
                            "source_exists": has_valid_source,
                            "target_exists": has_valid_target,
                        }
                    )

            edges = valid_edges

            if orphaned_edges:
                logger.warning(
                    f"  ⚠️ Found {len(orphaned_edges)} orphaned edges (will be filtered out)"
                )
                for orphan in orphaned_edges[:5]:  # Log first 5 only
                    logger.warning(
                        f"    - Edge {orphan['id']}: source={orphan['source']} (exists={orphan['source_exists']}), target={orphan['target']} (exists={orphan['target_exists']})"
                    )

            logger.info(
                f"  ✓ Found {len(edges)} valid edges ({len(orphaned_edges)} orphaned edges filtered)"
            )

        # Construire le résultat avec l'objet DSLGraph complet
        result = {
            "dsl": dsl,  # Retourner l'objet complet, pas to_graph_dict()
            "nodes": nodes,  # Chaque node utilise to_graph_dict()
            "edges": edges,  # Chaque edge utilise to_graph_dict()
            "edgeConstraints": dsl.allowed_edge_types,  # Edge type constraints from the graph
        }

        logger.info(f"✅ Complete graph: {len(nodes)} nodes, {len(edges)} edges")
        return result
