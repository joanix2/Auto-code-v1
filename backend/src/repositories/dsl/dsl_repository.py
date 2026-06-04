import logging
from typing import Any

from src.models.dsl import DSLGraph

from ..base import BaseRepository, convert_neo4j_types, prepare_neo4j_properties

logger = logging.getLogger(__name__)


class DSLRepository(BaseRepository[DSLGraph]):
    def __init__(self, db):
        super().__init__(db, DSLGraph, "DSLGraph")

    async def create(self, data: dict[str, Any]) -> DSLGraph:
        """
        Create a new dsl with OWNS relationship to owner

        Args:
            data: DSLGraph data including owner_id

        Returns:
            Created dsl
        """
        logger.info(f"🔍 Creating dsl: {data.get('name')}")
        logger.info(f"🔍 Owner ID: {data.get('owner_id')}")

        # Prepare data for Neo4j
        prepared_data = prepare_neo4j_properties(data)

        # Extract owner_id for relationship creation
        owner_id = prepared_data.get("owner_id")

        # Create dsl node and OWNS relationship if owner exists
        if owner_id:
            query = f"""
            // Create dsl node
            CREATE (m:{self.label} $props)
            SET m.created_at = datetime()
            
            // Find owner and create OWNS relationship
            WITH m
            MATCH (u:User {{username: $owner_id}})
            CREATE (u)-[r:OWNS]->(m)
            
            RETURN m
            """
            params = {"props": prepared_data, "owner_id": owner_id}
        else:
            # Fallback to standard creation without relationship
            query = f"""
            CREATE (m:{self.label} $props)
            SET m.created_at = datetime()
            RETURN m
            """
            params = {"props": prepared_data}

        result = self.db.execute_query(query, params)

        if not result:
            raise ValueError(f"Failed to create {self.label}")

        node = convert_neo4j_types(result[0]["m"])
        logger.info(f"✅ Created {self.label} with id={node.get('id')} and OWNS relationship")
        return self.model(**node)

    async def get_by_name(self, name: str) -> DSLGraph | None:
        """Get a dsl by name"""
        logger.info(f"🔍 Getting dsl by name: {name}")

        query = """
        MATCH (m:DSLGraph {name: $name})
        RETURN m
        """

        result = self.db.execute_query(query, {"name": name})
        logger.info(f"🔍 Result from Neo4j: {result}")

        if not result or len(result) == 0:
            logger.info(f"✅ No dsl found with name: {name}")
            return None

        node_data = convert_neo4j_types(result[0]["m"])
        logger.info(f"✅ Found dsl: {node_data}")
        return self.model(**node_data)

    async def get_by_status(self, status: str) -> list[DSLGraph]:
        """Get all dsls with a specific status"""
        logger.info(f"🔍 Getting dsls with status: {status}")

        query = """
        MATCH (m:DSLGraph {status: $status})
        RETURN m
        ORDER BY m.created_at DESC
        """

        result = self.db.execute_query(query, {"status": status})

        if not result:
            return []

        return [self.model(**convert_neo4j_types(record["m"])) for record in result]

    async def get_by_author(self, author: str) -> list[DSLGraph]:
        """Get all dsls by author (owner_id)"""
        logger.info(f"🔍 Getting dsls by author: {author}")

        query = """
        MATCH (m:DSLGraph {owner_id: $author})
        RETURN m
        ORDER BY m.created_at DESC
        """

        result = self.db.execute_query(query, {"author": author})

        if not result:
            return []

        return [self.model(**convert_neo4j_types(record["m"])) for record in result]
