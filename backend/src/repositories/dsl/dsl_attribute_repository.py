"""
DSLAttribute Repository - Database operations for attributes
"""

import logging
from typing import Any

from src.models.dsl.dsl_attribute import DSLAttribute
from src.models.dsl.dsl_config import ATTRIBUTE_NODE_TYPE

from ..base import BaseRepository, convert_neo4j_types, prepare_neo4j_properties

logger = logging.getLogger(__name__)


class DSLAttributeRepository(BaseRepository[DSLAttribute]):
    """Repository for attribute CRUD operations"""

    def __init__(self, db):
        super().__init__(db, DSLAttribute, "DSLAttribute")

    def _add_node_type(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add node_type to attribute data"""
        data["node_type"] = ATTRIBUTE_NODE_TYPE
        return data

    async def create(self, data: dict[str, Any]) -> DSLAttribute:
        """
        Create a new attribute with HAS_ATTRIBUTE relationship to dsl

        Args:
            data: DSLAttribute data including graph_id (dsl ID)

        Returns:
            Created attribute
        """
        logger.info(f"🔍 Creating attribute: {data.get('name')}")

        # Prepare data for Neo4j
        prepared_data = prepare_neo4j_properties(data)

        # Extract graph_id for relationship creation
        graph_id = prepared_data.get("graph_id")

        # Create attribute node and HAS_ATTRIBUTE relationship with dsl
        if graph_id:
            query = f"""
            // Create attribute node
            CREATE (a:{self.label} $props)
            SET a.created_at = datetime()
            
            // Find dsl and create HAS_ATTRIBUTE relationship
            WITH a
            MATCH (m:DSLGraph {{id: $graph_id}})
            CREATE (m)-[r:HAS_ATTRIBUTE]->(a)
            
            RETURN a
            """
            params = {"props": prepared_data, "graph_id": graph_id}
        else:
            # Fallback to standard creation without relationship
            query = f"""
            CREATE (a:{self.label} $props)
            SET a.created_at = datetime()
            RETURN a
            """
            params = {"props": prepared_data}

        result = self.db.execute_query(query, params)

        if not result:
            raise ValueError(f"Failed to create {self.label}")

        node = convert_neo4j_types(result[0]["a"])
        logger.info(
            f"✅ Created {self.label} with id={node.get('id')} and HAS_ATTRIBUTE relationship"
        )
        return self.model(**self._add_node_type(node))

    async def create_with_relationship(self, data: dict[str, Any]) -> DSLAttribute:
        """
        Create an attribute and link it to its concept AND dsl

        Args:
            data: DSLAttribute data including concept_id and graph_id

        Returns:
            Created attribute
        """
        concept_id = data.get("concept_id")
        graph_id = data.get("graph_id")

        if not concept_id:
            raise ValueError("concept_id is required for create_with_relationship")

        # Prepare data for Neo4j
        prepared_data = prepare_neo4j_properties(data)

        # Create attribute with relationships to both concept and dsl
        if graph_id:
            query = """
            // Create attribute node
            CREATE (a:DSLAttribute $props)
            SET a.created_at = datetime()
            
            // Link to concept
            WITH a
            MATCH (c:DSLConcept {id: $concept_id})
            CREATE (a)-[:ATTRIBUTE_OF]->(c)
            
            // Link to dsl
            WITH a
            MATCH (m:DSLGraph {id: $graph_id})
            CREATE (m)-[:HAS_ATTRIBUTE]->(a)
            
            RETURN a
            """
            params = {"props": prepared_data, "concept_id": concept_id, "graph_id": graph_id}
        else:
            # Only link to concept if no dsl
            query = """
            MATCH (c:DSLConcept {id: $concept_id})
            CREATE (a:DSLAttribute $props)
            SET a.created_at = datetime()
            CREATE (a)-[:ATTRIBUTE_OF]->(c)
            RETURN a
            """
            params = {"props": prepared_data, "concept_id": concept_id}

        result = self.db.execute_query(query, params)
        if not result:
            raise ValueError("Failed to create DSLAttribute")

        node = convert_neo4j_types(result[0]["a"])
        logger.info(
            f"✅ Created DSLAttribute with id={node.get('id')} for concept={concept_id}, dsl={graph_id}"
        )
        return self.model(**self._add_node_type(node))

    async def get_by_concept(
        self, concept_id: str, skip: int = 0, limit: int = 100
    ) -> list[DSLAttribute]:
        """
        Get all attributes for a specific concept

        Args:
            concept_id: DSLConcept ID
            skip: Number to skip
            limit: Max results

        Returns:
            List of attributes
        """
        query = """
        MATCH (a:DSLAttribute)-[:ATTRIBUTE_OF]->(c:DSLConcept {id: $concept_id})
        RETURN a
        ORDER BY a.created_at ASC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(
            query, {"concept_id": concept_id, "skip": skip, "limit": limit}
        )
        return [self.model(**self._add_node_type(convert_neo4j_types(row["a"]))) for row in result]

    async def get_by_dsl(
        self, dsl_id: str, skip: int = 0, limit: int = 100
    ) -> list[DSLAttribute]:
        """
        Get all attributes for a specific dsl

        Args:
            dsl_id: DSLGraph ID
            skip: Number to skip
            limit: Max results

        Returns:
            List of attributes
        """
        query = """
        MATCH (m:DSLGraph {id: $dsl_id})-[:HAS_ATTRIBUTE]->(a:DSLAttribute)
        RETURN a
        ORDER BY a.created_at ASC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(
            query, {"dsl_id": dsl_id, "skip": skip, "limit": limit}
        )
        return [self.model(**self._add_node_type(convert_neo4j_types(row["a"]))) for row in result]

    async def get_by_name(self, concept_id: str, name: str) -> DSLAttribute | None:
        """
        Get attribute by name within a concept

        Args:
            concept_id: DSLConcept ID
            name: DSLAttribute name

        Returns:
            DSLAttribute or None
        """
        query = """
        MATCH (a:DSLAttribute {name: $name})-[:ATTRIBUTE_OF]->(c:DSLConcept {id: $concept_id})
        RETURN a
        """
        result = self.db.execute_query(query, {"concept_id": concept_id, "name": name})
        if not result:
            return None
        return self.model(**self._add_node_type(convert_neo4j_types(result[0]["a"])))

    async def get_required_attributes(self, concept_id: str) -> list[DSLAttribute]:
        """
        Get all required attributes for a concept

        Args:
            concept_id: DSLConcept ID

        Returns:
            List of required attributes
        """
        query = """
        MATCH (a:DSLAttribute {is_required: true})-[:ATTRIBUTE_OF]->(c:DSLConcept {id: $concept_id})
        RETURN a
        ORDER BY a.created_at ASC
        """
        result = self.db.execute_query(query, {"concept_id": concept_id})
        return [self.model(**self._add_node_type(convert_neo4j_types(row["a"]))) for row in result]

    async def count_by_concept(self, concept_id: str) -> int:
        """
        Count attributes for a concept

        Args:
            concept_id: DSLConcept ID

        Returns:
            Number of attributes
        """
        query = """
        MATCH (a:DSLAttribute)-[:ATTRIBUTE_OF]->(c:DSLConcept {id: $concept_id})
        RETURN count(a) as count
        """
        result = self.db.execute_query(query, {"concept_id": concept_id})
        return result[0]["count"] if result else 0

    async def delete_all_by_dsl(self, dsl_id: str) -> int:
        """Delete all attributes for a dsl."""
        query = """
        MATCH (a:DSLAttribute {graph_id: $dsl_id})
        WITH a, count(a) as node_count
        DETACH DELETE a
        RETURN node_count as deleted
        """
        result = self.db.execute_query(query, {"dsl_id": dsl_id})
        deleted = result[0]["deleted"] if result else 0
        logger.info(f"Deleted {deleted} attributes for dsl {dsl_id}")
        return deleted

    async def delete(self, entity_id: str) -> bool:
        """
        Delete an attribute and its relationship

        Args:
            entity_id: DSLAttribute ID

        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (a:DSLAttribute {id: $id})
        DETACH DELETE a
        RETURN count(a) as deleted
        """
        result = self.db.execute_query(query, {"id": entity_id})
        deleted = result[0]["deleted"] > 0

        if deleted:
            logger.info(f"Deleted DSLAttribute with id={entity_id}")
        else:
            logger.warning(f"DSLAttribute with id={entity_id} not found for deletion")

        return deleted
