"""
Relationship Repository - Database operations for relationships between concepts
"""
from typing import Optional, List, Dict, Any
import logging

from ..base import BaseRepository, convert_neo4j_types
from src.models.MDE.relationship import Relationship, RelationshipType

logger = logging.getLogger(__name__)


class RelationshipRepository(BaseRepository[Relationship]):
    """Repository for relationship CRUD operations"""

    def __init__(self, db):
        super().__init__(db, Relationship, "Relationship")

    async def create_with_concepts(self, data: Dict[str, Any]) -> Relationship:
        """
        Create a relationship and link it between two concepts
        
        Args:
            data: Relationship data including source_concept_id and target_concept_id
            
        Returns:
            Created relationship
        """
        source_id = data.get("source_concept_id")
        target_id = data.get("target_concept_id")
        
        if not source_id or not target_id:
            raise ValueError("source_concept_id and target_concept_id are required")

        # Get target concept name if not provided
        target_name = data.get("target_concept_name")
        if not target_name:
            query_target = """
            MATCH (c:Concept {id: $target_id})
            RETURN c.name as name
            """
            result = self.db.execute_query(query_target, {"target_id": target_id})
            if result:
                target_name = result[0]["name"]
                data["target_concept_name"] = target_name

        query = """
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        CREATE (r:Relationship $props)
        SET r.created_at = datetime()
        CREATE (source)-[:RELATES_TO {relationship_id: r.id}]->(target)
        RETURN r
        """
        result = self.db.execute_query(
            query, 
            {"source_id": source_id, "target_id": target_id, "props": data}
        )
        if not result:
            raise ValueError("Failed to create Relationship")
        
        node = convert_neo4j_types(result[0]["r"])
        logger.info(f"Created Relationship with id={node.get('id')} from {source_id} to {target_id}")
        return self.model(**node)

    async def get_by_metamodel(self, metamodel_id: str, skip: int = 0, limit: int = 100) -> List[Relationship]:
        """
        Get all relationships for a specific metamodel
        
        Args:
            metamodel_id: Metamodel ID
            skip: Number to skip
            limit: Max results
            
        Returns:
            List of relationships
        """
        query = """
        MATCH (r:Relationship {metamodel_id: $metamodel_id})
        RETURN r
        ORDER BY r.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "skip": skip, "limit": limit})
        return [self.model(**convert_neo4j_types(row["r"])) for row in result]

    async def get_by_source_concept(self, source_concept_id: str) -> List[Relationship]:
        """
        Get all relationships from a source concept
        
        Args:
            source_concept_id: Source concept ID
            
        Returns:
            List of relationships
        """
        query = """
        MATCH (r:Relationship {source_concept_id: $source_id})
        RETURN r
        ORDER BY r.created_at ASC
        """
        result = self.db.execute_query(query, {"source_id": source_concept_id})
        return [self.model(**convert_neo4j_types(row["r"])) for row in result]

    async def get_by_target_concept(self, target_concept_id: str) -> List[Relationship]:
        """
        Get all relationships to a target concept
        
        Args:
            target_concept_id: Target concept ID
            
        Returns:
            List of relationships
        """
        query = """
        MATCH (r:Relationship {target_concept_id: $target_id})
        RETURN r
        ORDER BY r.created_at ASC
        """
        result = self.db.execute_query(query, {"target_id": target_concept_id})
        return [self.model(**convert_neo4j_types(row["r"])) for row in result]

    async def get_by_type(self, metamodel_id: str, relationship_type: RelationshipType) -> List[Relationship]:
        """
        Get all relationships of a specific type in a metamodel
        
        Args:
            metamodel_id: Metamodel ID
            relationship_type: Type of relationship
            
        Returns:
            List of relationships
        """
        query = """
        MATCH (r:Relationship {metamodel_id: $metamodel_id, type: $type})
        RETURN r
        ORDER BY r.created_at ASC
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "type": relationship_type.value})
        return [self.model(**convert_neo4j_types(row["r"])) for row in result]

    async def get_between_concepts(self, source_id: str, target_id: str) -> Optional[Relationship]:
        """
        Get relationship between two specific concepts
        
        Args:
            source_id: Source concept ID
            target_id: Target concept ID
            
        Returns:
            Relationship or None
        """
        query = """
        MATCH (r:Relationship {source_concept_id: $source_id, target_concept_id: $target_id})
        RETURN r
        """
        result = self.db.execute_query(query, {"source_id": source_id, "target_id": target_id})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["r"]))

    async def count_by_metamodel(self, metamodel_id: str) -> int:
        """
        Count relationships in a metamodel
        
        Args:
            metamodel_id: Metamodel ID
            
        Returns:
            Number of relationships
        """
        query = """
        MATCH (r:Relationship {metamodel_id: $metamodel_id})
        RETURN count(r) as count
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id})
        return result[0]["count"] if result else 0

    async def delete(self, entity_id: str) -> bool:
        """
        Delete a relationship and its graph edge
        
        Args:
            entity_id: Relationship ID
            
        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (r:Relationship {id: $id})
        OPTIONAL MATCH ()-[edge:RELATES_TO {relationship_id: $id}]->()
        DELETE edge, r
        RETURN count(r) as deleted
        """
        result = self.db.execute_query(query, {"id": entity_id})
        deleted = result[0]["deleted"] > 0
        
        if deleted:
            logger.info(f"Deleted Relationship with id={entity_id}")
        else:
            logger.warning(f"Relationship with id={entity_id} not found for deletion")
        
        return deleted
