"""
Concept Repository - Database operations for concepts
"""
from typing import Optional, List, Dict, Any
import logging

from ...base import BaseRepository, convert_neo4j_types, prepare_neo4j_properties
from src.models.MDE.M2.concept import Concept
from src.models.MDE.M3.m3_config import CONCEPT_NODE_TYPE

logger = logging.getLogger(__name__)


class ConceptRepository(BaseRepository[Concept]):
    """Repository for concept CRUD operations"""

    def __init__(self, db):
        super().__init__(db, Concept, "Concept")

    def _add_node_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add node_type to concept data"""
        data["node_type"] = CONCEPT_NODE_TYPE
        return data

    async def create(self, data: Dict[str, Any]) -> Concept:
        """
        Create a new concept with HAS_CONCEPT relationship to metamodel
        
        Args:
            data: Concept data including graph_id (metamodel ID)
            
        Returns:
            Created concept
        """
        logger.info(f"🔍 Creating concept: {data.get('name')}")
        
        # Prepare data for Neo4j
        prepared_data = prepare_neo4j_properties(data)
        
        # Extract graph_id for relationship creation
        graph_id = prepared_data.get('graph_id')
        
        # Create concept node and HAS_CONCEPT relationship
        if graph_id:
            query = f"""
            // Create concept node
            CREATE (c:{self.label} $props)
            SET c.created_at = datetime()
            
            // Find metamodel and create HAS_CONCEPT relationship
            WITH c
            MATCH (m:Metamodel {{id: $graph_id}})
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
        logger.info(f"✅ Created {self.label} with id={node.get('id')} and HAS_CONCEPT relationship")
        return self.model(**self._add_node_type(node))

    async def get_by_metamodel(self, metamodel_id: str, skip: int = 0, limit: int = 100) -> List[Concept]:
        """
        Get all concepts for a specific metamodel
        
        Args:
            metamodel_id: Metamodel ID (graph_id)
            skip: Number to skip
            limit: Max results
            
        Returns:
            List of concepts
        """
        query = """
        MATCH (c:Concept {graph_id: $metamodel_id})
        RETURN c
        ORDER BY c.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "skip": skip, "limit": limit})
        return [self.model(**self._add_node_type(convert_neo4j_types(row["c"]))) for row in result]

    async def get_by_name(self, metamodel_id: str, name: str) -> Optional[Concept]:
        """
        Get concept by name within a metamodel
        
        Args:
            metamodel_id: Metamodel ID (graph_id)
            name: Concept name
            
        Returns:
            Concept or None
        """
        query = """
        MATCH (c:Concept {graph_id: $metamodel_id, name: $name})
        RETURN c
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "name": name})
        if not result:
            return None
        return self.model(**self._add_node_type(convert_neo4j_types(result[0]["c"])))

    async def update_position(self, concept_id: str, x: float, y: float) -> Optional[Concept]:
        """
        Update concept position in graph
        
        Args:
            concept_id: Concept ID
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Updated concept or None
        """
        query = """
        MATCH (c:Concept {id: $id})
        SET c.x = $x, c.y = $y
        SET c.updated_at = datetime()
        RETURN c
        """
        result = self.db.execute_query(query, {"id": concept_id, "x": x, "y": y})
        if not result:
            return None
        return self.model(**self._add_node_type(convert_neo4j_types(result[0]["c"])))

    async def get_with_attributes(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Get concept with all its attributes
        
        Args:
            concept_id: Concept ID
            
        Returns:
            Dict with concept and attributes list
        """
        query = """
        MATCH (c:Concept {id: $id})
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
            "attributes": attributes
        }

    async def count_by_metamodel(self, metamodel_id: str) -> int:
        """
        Count concepts in a metamodel
        
        Args:
            metamodel_id: Metamodel ID
            
        Returns:
            Number of concepts
        """
        query = """
        MATCH (c:Concept {metamodel_id: $metamodel_id})
        RETURN count(c) as count
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id})
        return result[0]["count"] if result else 0

    async def delete(self, entity_id: str) -> bool:
        """
        Delete a concept and all its relationships
        
        Uses DETACH DELETE to automatically remove all relationships
        before deleting the node.
        
        Args:
            entity_id: Concept ID
            
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
