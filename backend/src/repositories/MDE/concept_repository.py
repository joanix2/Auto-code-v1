"""
Concept Repository - Database operations for concepts
"""
from typing import Optional, List, Dict, Any
import logging

from ..base import BaseRepository, convert_neo4j_types
from src.models.MDE.concept import Concept

logger = logging.getLogger(__name__)


class ConceptRepository(BaseRepository[Concept]):
    """Repository for concept CRUD operations"""

    def __init__(self, db):
        super().__init__(db, Concept, "Concept")

    async def get_by_metamodel(self, metamodel_id: str, skip: int = 0, limit: int = 100) -> List[Concept]:
        """
        Get all concepts for a specific metamodel
        
        Args:
            metamodel_id: Metamodel ID
            skip: Number to skip
            limit: Max results
            
        Returns:
            List of concepts
        """
        query = """
        MATCH (c:Concept {metamodel_id: $metamodel_id})
        RETURN c
        ORDER BY c.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "skip": skip, "limit": limit})
        return [self.model(**convert_neo4j_types(row["c"])) for row in result]

    async def get_by_name(self, metamodel_id: str, name: str) -> Optional[Concept]:
        """
        Get concept by name within a metamodel
        
        Args:
            metamodel_id: Metamodel ID
            name: Concept name
            
        Returns:
            Concept or None
        """
        query = """
        MATCH (c:Concept {metamodel_id: $metamodel_id, name: $name})
        RETURN c
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "name": name})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["c"]))

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
        return self.model(**convert_neo4j_types(result[0]["c"]))

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
            "concept": self.model(**concept_data),
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
