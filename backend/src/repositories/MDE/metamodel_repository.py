from typing import List, Optional
from src.repositories.base import BaseRepository, convert_neo4j_types
from src.models.MDE.metamodel import Metamodel, MetamodelCreate, MetamodelUpdate
import logging

logger = logging.getLogger(__name__)


class MetamodelRepository(BaseRepository[Metamodel]):
    def __init__(self, db):
        super().__init__(db, Metamodel, "Metamodel")

    def _create_node_query(self, data: MetamodelCreate) -> str:
        """Generate Cypher query for creating a metamodel node"""
        return """
        CREATE (m:Metamodel {
            id: randomUUID(),
            name: $name,
            description: $description,
            version: $version,
            node_count: $node_count,
            edge_count: $edge_count,
            author: $author,
            status: $status,
            created_at: datetime(),
            updated_at: null
        })
        RETURN m
        """

    def _update_node_query(self) -> str:
        """Generate Cypher query for updating a metamodel node"""
        return """
        MATCH (m:Metamodel {id: $id})
        SET m.updated_at = datetime()
        """

    async def get_by_name(self, name: str) -> Optional[Metamodel]:
        """Get a metamodel by name"""
        logger.info(f"🔍 Getting metamodel by name: {name}")
        
        query = """
        MATCH (m:Metamodel {name: $name})
        RETURN m
        """
        
        result = self.db.execute_query(query, {"name": name})
        logger.info(f"🔍 Result from Neo4j: {result}")
        
        if not result or len(result) == 0:
            logger.info(f"✅ No metamodel found with name: {name}")
            return None
        
        node_data = convert_neo4j_types(result[0]["m"])
        logger.info(f"✅ Found metamodel: {node_data}")
        return self.model(**node_data)

    async def get_by_status(self, status: str) -> List[Metamodel]:
        """Get all metamodels with a specific status"""
        logger.info(f"🔍 Getting metamodels with status: {status}")
        
        query = """
        MATCH (m:Metamodel {status: $status})
        RETURN m
        ORDER BY m.created_at DESC
        """
        
        result = self.db.execute_query(query, {"status": status})
        
        if not result:
            return []
        
        return [self.model(**convert_neo4j_types(record["m"])) for record in result]

    async def get_by_author(self, author: str) -> List[Metamodel]:
        """Get all metamodels by author"""
        logger.info(f"🔍 Getting metamodels by author: {author}")
        
        query = """
        MATCH (m:Metamodel {author: $author})
        RETURN m
        ORDER BY m.created_at DESC
        """
        
        result = self.db.execute_query(query, {"author": author})
        
        if not result:
            return []
        
        return [self.model(**convert_neo4j_types(record["m"])) for record in result]
