"""
DSLConcept Repository - Database operations for concepts
"""

import logging
from typing import Any

from src.models.dsl.dsl_concept import DSLConcept
from src.models.dsl.dsl_config import CONCEPT_NODE_TYPE

from ..base import BaseRepository, convert_neo4j_types, prepare_neo4j_properties

logger = logging.getLogger(__name__)


class DSLConceptRepository(BaseRepository[DSLConcept]):
    """Repository for concept CRUD operations"""

    def __init__(self, db):
        super().__init__(db, DSLConcept, "DSLConcept")

    def _add_node_type(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add node_type to concept data"""
        data["node_type"] = CONCEPT_NODE_TYPE
        return data

    async def create(self, data: dict[str, Any]) -> DSLConcept:
        """
        Create a new concept with HAS_CONCEPT relationship to dsl

        Args:
            data: DSLConcept data including graph_id (dsl ID)

        Returns:
            Created concept
        """
        logger.info(f"🔍 Creating concept: {data.get('name')}")

        # Prepare data for Neo4j
        prepared_data = prepare_neo4j_properties(data)

        # Extract graph_id for relationship creation
        graph_id = prepared_data.get("graph_id")

        # Create concept node and HAS_CONCEPT relationship
        if graph_id:
            query = f"""
            // Create concept node
            CREATE (c:{self.label} $props)
            SET c.created_at = datetime()
            
            // Find dsl and create HAS_CONCEPT relationship
            WITH c
            MATCH (m:DSLGraph {{id: $graph_id}})
            CREATE (m)-[r:HAS_CONCEPT]->(c)
            
            RETURN c
            """
            params = {"props": prepared_data, "graph_id": graph_id}
        else:
            # Fallback to standard creation without relationship
            query = f"""
            CREATE (c:{self.label} $props)
            SET c.created_at = datetime()
            RETURN c
            """
            params = {"props": prepared_data}

        result = self.db.execute_query(query, params)

        if not result:
            raise ValueError(f"Failed to create {self.label}")

        node = convert_neo4j_types(result[0]["c"])
        logger.info(
            f"✅ Created {self.label} with id={node.get('id')} and HAS_CONCEPT relationship"
        )
        return self.model(**self._add_node_type(node))

    async def get_by_dsl(
        self, dsl_id: str, skip: int = 0, limit: int = 100
    ) -> list[DSLConcept]:
        """
        Get all concepts for a specific dsl

        Args:
            dsl_id: DSLGraph ID (graph_id)
            skip: Number to skip
            limit: Max results

        Returns:
            List of concepts
        """
        query = """
        MATCH (c:DSLConcept {graph_id: $dsl_id})
        RETURN c
        ORDER BY c.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(
            query, {"dsl_id": dsl_id, "skip": skip, "limit": limit}
        )
        return [self.model(**self._add_node_type(convert_neo4j_types(row["c"]))) for row in result]

    async def get_by_name(self, dsl_id: str, name: str) -> DSLConcept | None:
        """
        Get concept by name within a dsl

        Args:
            dsl_id: DSLGraph ID (graph_id)
            name: DSLConcept name

        Returns:
            DSLConcept or None
        """
        query = """
        MATCH (c:DSLConcept {graph_id: $dsl_id, name: $name})
        RETURN c
        """
        result = self.db.execute_query(query, {"dsl_id": dsl_id, "name": name})
        if not result:
            return None
        return self.model(**self._add_node_type(convert_neo4j_types(result[0]["c"])))

    async def update_position(self, concept_id: str, x: float, y: float) -> DSLConcept | None:
        """
        Update concept position in graph

        Args:
            concept_id: DSLConcept ID
            x: X coordinate
            y: Y coordinate

        Returns:
            Updated concept or None
        """
        query = """
        MATCH (c:DSLConcept {id: $id})
        SET c.x = $x, c.y = $y
        SET c.updated_at = datetime()
        RETURN c
        """
        result = self.db.execute_query(query, {"id": concept_id, "x": x, "y": y})
        if not result:
            return None
        return self.model(**self._add_node_type(convert_neo4j_types(result[0]["c"])))

    async def get_with_attributes(self, concept_id: str) -> dict[str, Any] | None:
        """
        Get concept with all its attributes

        Args:
            concept_id: DSLConcept ID

        Returns:
            Dict with concept and attributes list
        """
        query = """
        MATCH (c:DSLConcept {id: $id})
        OPTIONAL MATCH (c)<-[:ATTRIBUTE_OF]-(a:Attribute)
        RETURN c, collect(a) as attributes
        """
        result = self.db.execute_query(query, {"id": concept_id})
        if not result:
            return None

        concept_data = convert_neo4j_types(result[0]["c"])
        attributes = [convert_neo4j_types(attr) for attr in result[0]["attributes"] if attr]

        return {
            "concept": self.model(**self._add_node_type(concept_data)),
            "attributes": attributes,
        }

    async def count_by_dsl(self, dsl_id: str) -> int:
        """
        Count concepts in a dsl

        Args:
            dsl_id: DSLGraph ID

        Returns:
            Number of concepts
        """
        query = """
        MATCH (c:DSLConcept {dsl_id: $dsl_id})
        RETURN count(c) as count
        """
        result = self.db.execute_query(query, {"dsl_id": dsl_id})
        return result[0]["count"] if result else 0

    async def delete_all_by_dsl(self, dsl_id: str) -> int:
        """
        Delete all concepts for a dsl.
        Uses DETACH DELETE to cascade-remove all connected edges.

        Args:
            dsl_id: DSLGraph ID (graph_id)

        Returns:
            Number of deleted concepts
        """
        query = """
        MATCH (c:DSLConcept {graph_id: $dsl_id})
        WITH c, count(c) as node_count
        DETACH DELETE c
        RETURN node_count as deleted
        """
        result = self.db.execute_query(query, {"dsl_id": dsl_id})
        deleted = result[0]["deleted"] if result else 0
        logger.info(f"Deleted {deleted} concepts for dsl {dsl_id}")
        return deleted

    async def delete(self, entity_id: str) -> bool:
        """
        Delete a concept and all its relationships

        Uses DETACH DELETE to automatically remove all relationships
        before deleting the node.

        Args:
            entity_id: DSLConcept ID

        Returns:
            True if deleted, False if not found
        """
        query = f"""
        MATCH (c:{self.label} {{id: $id}})
        WITH c, count(c) as node_count
        DETACH DELETE c
        RETURN node_count as deleted
        """
        logger.info(f"🗑️ Attempting to delete {self.label} with id={entity_id}")
        result = self.db.execute_query(query, {"id": entity_id})
        logger.info(f"🔍 Delete query result: {result}")

        deleted = result and len(result) > 0 and result[0]["deleted"] > 0

        if deleted:
            logger.info(f"✅ Deleted {self.label} with id={entity_id} and all its relationships")
        else:
            logger.warning(f"⚠️ {self.label} with id={entity_id} not found for deletion")

        return deleted
