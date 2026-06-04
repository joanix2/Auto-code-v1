"""
DSLRelation Repository - Database operations for relationships between concepts
"""

import logging
from typing import Any

from src.models.dsl.dsl_relation import DSLRelation, DSLRelationType
from src.models.dsl.dsl_config import RELATION_NODE_TYPE

from ..base import BaseRepository, convert_neo4j_types

logger = logging.getLogger(__name__)


class DSLRelationRepository(BaseRepository[DSLRelation]):
    """Repository for relationship CRUD operations"""

    def __init__(self, db):
        super().__init__(db, DSLRelation, "DSLRelation")

    def _add_node_type(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add node_type to relationship data"""
        data["node_type"] = RELATION_NODE_TYPE
        return data

    def _normalize_relationship_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize relationship data to match Node model fields
        DSLRelation is a Node, not an Edge
        """
        normalized = {**data}

        # Ensure graph_id is set from dsl_id if present
        if "dsl_id" in normalized and "graph_id" not in normalized:
            normalized["graph_id"] = normalized["dsl_id"]

        # Add node_type from M3 configuration
        normalized["node_type"] = RELATION_NODE_TYPE

        return normalized

    async def create_standalone(self, data: dict[str, Any]) -> DSLRelation:
        """
        Create a relationship node without DOMAIN/RANGE connections

        Les connexions DOMAIN/RANGE seront créées séparément via le système d'edges.
        Cette méthode crée uniquement le noeud DSLRelation.

        Structure in Neo4j:
        (DSLGraph)-[:HAS_RELATION]->(DSLRelation:Node)

        Args:
            data: DSLRelation data including name, type, description

        Returns:
            Created relationship
        """
        dsl_id = data.get("dsl_id")
        name = data.get("name")

        if not dsl_id:
            raise ValueError("dsl_id is required")
        if not name:
            raise ValueError("name is required")

        # Prepare relationship node data
        rel_data = {
            "id": data.get("id"),
            "name": name,
            "type": data.get("type"),
            "description": data.get("description"),
            "graph_id": dsl_id,
            "x_position": data.get("x_position"),
            "y_position": data.get("y_position"),
        }

        # Create DSLRelation node
        query = """
        MATCH (dsl:DSLGraph {id: $dsl_id})
        CREATE (r:DSLRelation $props)
        SET r.created_at = datetime()
        CREATE (dsl)-[:HAS_RELATION]->(r)
        RETURN r
        """
        result = self.db.execute_query(query, {"dsl_id": dsl_id, "props": rel_data})
        if not result:
            raise ValueError("Failed to create DSLRelation")

        node = convert_neo4j_types(result[0]["r"])
        logger.info(f"Created standalone DSLRelation '{node.get('name')}' (id={node.get('id')})")
        return self.model(**self._normalize_relationship_data(node))

    async def create_with_concepts(self, data: dict[str, Any]) -> DSLRelation:
        """
        Create a relationship node and link it with DOMAIN and RANGE edges

        Structure in Neo4j:
        (DSLGraph)-[:HAS_RELATION]->(DSLRelation:Node)
        (DSLRelation)-[:DOMAIN]->(SourceDSLConcept)
        (DSLRelation)-[:RANGE]->(TargetDSLConcept)

        Args:
            data: DSLRelation data with source_id and target_id in the dict

        Returns:
            Created relationship
        """
        dsl_id = data.get("dsl_id")
        name = data.get("name")
        # Ces IDs viennent du dict data, pas du modèle DSLRelation
        source_id = data.get("source_id")
        target_id = data.get("target_id")

        if not source_id or not target_id:
            raise ValueError("source_id and target_id are required in data dict")

        # Prepare relationship data (it's a Node, not an Edge)
        rel_data = {
            "id": data.get("id"),
            "name": name,
            "type": data.get("type"),
            "description": data.get("description"),
            "graph_id": dsl_id,
            "x_position": data.get("x_position"),
            "y_position": data.get("y_position"),
        }

        # Create DSLRelation node with DOMAIN and RANGE edges
        query = """
        MATCH (dsl:DSLGraph {id: $dsl_id})
        MATCH (source:DSLConcept {id: $source_id})
        MATCH (target:DSLConcept {id: $target_id})
        CREATE (r:DSLRelation $props)
        SET r.created_at = datetime()
        CREATE (dsl)-[:HAS_RELATION]->(r)
        CREATE (r)-[:DOMAIN]->(source)
        CREATE (r)-[:RANGE]->(target)
        RETURN r
        """
        result = self.db.execute_query(
            query,
            {
                "dsl_id": dsl_id,
                "source_id": source_id,
                "target_id": target_id,
                "props": rel_data,
            },
        )
        if not result:
            raise ValueError("Failed to create DSLRelation")

        node = convert_neo4j_types(result[0]["r"])
        logger.info(
            f"Created DSLRelation '{node.get('name')}' (id={node.get('id')}) with DOMAIN/RANGE edges"
        )
        return self.model(**self._normalize_relationship_data(node))

    async def get_by_dsl(
        self, dsl_id: str, skip: int = 0, limit: int = 100
    ) -> list[DSLRelation]:
        """
        Get all relationships for a specific dsl via HAS_RELATION edge

        Args:
            dsl_id: DSLGraph ID
            skip: Number to skip
            limit: Max results

        Returns:
            List of relationships
        """
        query = """
        MATCH (m:DSLGraph {id: $dsl_id})-[:HAS_RELATION]->(r:DSLRelation)
        OPTIONAL MATCH (r)-[:DOMAIN]->(source:DSLConcept)
        OPTIONAL MATCH (r)-[:RANGE]->(target:DSLConcept)
        RETURN r, source.id as source_id, source.name as source_name, 
               target.id as target_id, target.name as target_name
        ORDER BY r.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(
            query, {"dsl_id": dsl_id, "skip": skip, "limit": limit}
        )

        relationships = []
        for row in result:
            rel_data = convert_neo4j_types(row["r"])
            # Add source and target info from the graph edges
            rel_data["source_id"] = row["source_id"]
            rel_data["source_label"] = row["source_name"]
            rel_data["target_id"] = row["target_id"]
            rel_data["target_label"] = row["target_name"]
            rel_data["graph_id"] = dsl_id

            relationships.append(self.model(**self._normalize_relationship_data(rel_data)))

        return relationships

    async def get_by_type(
        self, dsl_id: str, relationship_type: DSLRelationType
    ) -> list[DSLRelation]:
        """
        Get all relationships of a specific type in a dsl

        Args:
            dsl_id: DSLGraph ID
            relationship_type: Type of relationship

        Returns:
            List of relationships
        """
        query = """
        MATCH (m:DSLGraph {id: $dsl_id})-[:HAS_RELATION]->(r:DSLRelation {type: $type})
        OPTIONAL MATCH (r)-[:DOMAIN]->(source:DSLConcept)
        OPTIONAL MATCH (r)-[:RANGE]->(target:DSLConcept)
        RETURN r, source.id as source_id, source.name as source_name,
               target.id as target_id, target.name as target_name
        ORDER BY r.created_at ASC
        """
        result = self.db.execute_query(
            query, {"dsl_id": dsl_id, "type": relationship_type.value}
        )

        relationships = []
        for row in result:
            rel_data = convert_neo4j_types(row["r"])
            rel_data["source_id"] = row["source_id"]
            rel_data["source_label"] = row["source_name"]
            rel_data["target_id"] = row["target_id"]
            rel_data["target_label"] = row["target_name"]
            rel_data["graph_id"] = dsl_id
            relationships.append(self.model(**self._normalize_relationship_data(rel_data)))

        return relationships

    async def get_between_concepts(self, source_id: str, target_id: str) -> DSLRelation | None:
        """
        Get relationship between two specific concepts

        Args:
            source_id: Source concept ID
            target_id: Target concept ID

        Returns:
            DSLRelation or None
        """
        query = """
        MATCH (r:DSLRelation)-[:DOMAIN]->(source:DSLConcept {id: $source_id})
        MATCH (r)-[:RANGE]->(target:DSLConcept {id: $target_id})
        RETURN r, source.id as source_id, source.name as source_name,
               target.id as target_id, target.name as target_name
        """
        result = self.db.execute_query(query, {"source_id": source_id, "target_id": target_id})
        if not result:
            return None

        rel_data = convert_neo4j_types(result[0]["r"])
        rel_data["source_id"] = result[0]["source_id"]
        rel_data["source_label"] = result[0]["source_name"]
        rel_data["target_id"] = result[0]["target_id"]
        rel_data["target_label"] = result[0]["target_name"]

        return self.model(**self._normalize_relationship_data(rel_data))

    async def get_by_source_concept(self, concept_id: str) -> list[DSLRelation]:
        """Get relationships where this concept is the source (DOMAIN)"""
        query = """
        MATCH (r:DSLRelation)-[:DOMAIN]->(source:DSLConcept {id: $concept_id})
        OPTIONAL MATCH (r)-[:RANGE]->(target:DSLConcept)
        RETURN r, target.id as target_id, target.name as target_name
        ORDER BY r.created_at DESC
        """
        result = self.db.execute_query(query, {"concept_id": concept_id})
        rels = []
        for row in result:
            data = convert_neo4j_types(row["r"])
            data["source_id"] = concept_id
            data["target_id"] = row["target_id"]
            data["source_label"] = data.get("name")
            data["target_label"] = row["target_name"]
            rels.append(self.model(**self._normalize_relationship_data(data)))
        return rels

    async def get_by_target_concept(self, concept_id: str) -> list[DSLRelation]:
        """Get relationships where this concept is the target (RANGE)"""
        query = """
        MATCH (r:DSLRelation)-[:RANGE]->(target:DSLConcept {id: $concept_id})
        OPTIONAL MATCH (r)-[:DOMAIN]->(source:DSLConcept)
        RETURN r, source.id as source_id, source.name as source_name
        ORDER BY r.created_at DESC
        """
        result = self.db.execute_query(query, {"concept_id": concept_id})
        rels = []
        for row in result:
            data = convert_neo4j_types(row["r"])
            data["source_id"] = row["source_id"]
            data["target_id"] = concept_id
            data["source_label"] = row["source_name"]
            data["target_label"] = data.get("name")
            rels.append(self.model(**self._normalize_relationship_data(data)))
        return rels

    async def count_by_dsl(self, dsl_id: str) -> int:
        """
        Count relationships in a dsl via HAS_RELATION edge

        Args:
            dsl_id: DSLGraph ID

        Returns:
            Number of relationships
        """
        query = """
        MATCH (m:DSLGraph {id: $dsl_id})-[:HAS_RELATION]->(r:DSLRelation)
        RETURN count(r) as count
        """
        result = self.db.execute_query(query, {"dsl_id": dsl_id})
        return result[0]["count"] if result else 0

    async def delete_all_by_dsl(self, dsl_id: str) -> int:
        """Delete all relationships for a dsl."""
        query = """
        MATCH (r:DSLRelation {graph_id: $dsl_id})
        WITH r, count(r) as node_count
        DETACH DELETE r
        RETURN node_count as deleted
        """
        result = self.db.execute_query(query, {"dsl_id": dsl_id})
        deleted = result[0]["deleted"] if result else 0
        logger.info(f"Deleted {deleted} relationships for dsl {dsl_id}")
        return deleted

    async def delete(self, entity_id: str) -> bool:
        """
        Delete a relationship and its DOMAIN, RANGE, and HAS_RELATION edges

        Args:
            entity_id: DSLRelation ID

        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (r:DSLRelation {id: $id})
        OPTIONAL MATCH (m:DSLGraph)-[has:HAS_RELATION]->(r)
        OPTIONAL MATCH (r)-[domain:DOMAIN]->()
        OPTIONAL MATCH (r)-[range:RANGE]->()
        WITH r, has, domain, range, count(r) as node_count
        DELETE has, domain, range, r
        RETURN node_count as deleted
        """
        result = self.db.execute_query(query, {"id": entity_id})
        deleted = result and len(result) > 0 and result[0]["deleted"] > 0

        if deleted:
            logger.info(
                f"🗑️ Deleted DSLRelation with id={entity_id} and its edges (DOMAIN, RANGE, HAS_RELATION)"
            )
        else:
            logger.warning(f"⚠️ DSLRelation with id={entity_id} not found for deletion")

        return deleted
