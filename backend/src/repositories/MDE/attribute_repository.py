"""
Attribute Repository - Database operations for attributes
"""
from typing import Optional, List, Dict, Any
import logging

from ..base import BaseRepository, convert_neo4j_types
from src.models.MDE.attribute import Attribute

logger = logging.getLogger(__name__)


class AttributeRepository(BaseRepository[Attribute]):
    """Repository for attribute CRUD operations"""

    def __init__(self, db):
        super().__init__(db, Attribute, "Attribute")

    async def create_with_relationship(self, data: Dict[str, Any]) -> Attribute:
        """
        Create an attribute and link it to its concept
        
        Args:
            data: Attribute data including concept_id
            
        Returns:
            Created attribute
        """
        concept_id = data.get("concept_id")
        if not concept_id:
            raise ValueError("concept_id is required")

        query = """
        MATCH (c:Concept {id: $concept_id})
        CREATE (a:Attribute $props)
        SET a.created_at = datetime()
        CREATE (a)-[:ATTRIBUTE_OF]->(c)
        RETURN a
        """
        result = self.db.execute_query(query, {"concept_id": concept_id, "props": data})
        if not result:
            raise ValueError("Failed to create Attribute")
        
        node = convert_neo4j_types(result[0]["a"])
        logger.info(f"Created Attribute with id={node.get('id')} for concept={concept_id}")
        return self.model(**node)

    async def get_by_concept(self, concept_id: str, skip: int = 0, limit: int = 100) -> List[Attribute]:
        """
        Get all attributes for a specific concept
        
        Args:
            concept_id: Concept ID
            skip: Number to skip
            limit: Max results
            
        Returns:
            List of attributes
        """
        query = """
        MATCH (a:Attribute)-[:ATTRIBUTE_OF]->(c:Concept {id: $concept_id})
        RETURN a
        ORDER BY a.created_at ASC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(query, {"concept_id": concept_id, "skip": skip, "limit": limit})
        return [self.model(**convert_neo4j_types(row["a"])) for row in result]

    async def get_by_name(self, concept_id: str, name: str) -> Optional[Attribute]:
        """
        Get attribute by name within a concept
        
        Args:
            concept_id: Concept ID
            name: Attribute name
            
        Returns:
            Attribute or None
        """
        query = """
        MATCH (a:Attribute {name: $name})-[:ATTRIBUTE_OF]->(c:Concept {id: $concept_id})
        RETURN a
        """
        result = self.db.execute_query(query, {"concept_id": concept_id, "name": name})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["a"]))

    async def get_required_attributes(self, concept_id: str) -> List[Attribute]:
        """
        Get all required attributes for a concept
        
        Args:
            concept_id: Concept ID
            
        Returns:
            List of required attributes
        """
        query = """
        MATCH (a:Attribute {is_required: true})-[:ATTRIBUTE_OF]->(c:Concept {id: $concept_id})
        RETURN a
        ORDER BY a.created_at ASC
        """
        result = self.db.execute_query(query, {"concept_id": concept_id})
        return [self.model(**convert_neo4j_types(row["a"])) for row in result]

    async def count_by_concept(self, concept_id: str) -> int:
        """
        Count attributes for a concept
        
        Args:
            concept_id: Concept ID
            
        Returns:
            Number of attributes
        """
        query = """
        MATCH (a:Attribute)-[:ATTRIBUTE_OF]->(c:Concept {id: $concept_id})
        RETURN count(a) as count
        """
        result = self.db.execute_query(query, {"concept_id": concept_id})
        return result[0]["count"] if result else 0

    async def delete(self, entity_id: str) -> bool:
        """
        Delete an attribute and its relationship
        
        Args:
            entity_id: Attribute ID
            
        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (a:Attribute {id: $id})
        DETACH DELETE a
        RETURN count(a) as deleted
        """
        result = self.db.execute_query(query, {"id": entity_id})
        deleted = result[0]["deleted"] > 0
        
        if deleted:
            logger.info(f"Deleted Attribute with id={entity_id}")
        else:
            logger.warning(f"Attribute with id={entity_id} not found for deletion")
        
        return deleted
