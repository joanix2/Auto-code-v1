"""
Base repository with generic CRUD operations
"""
from typing import TypeVar, Generic, Optional, List, Type, Dict, Any
from pydantic import BaseModel
from abc import ABC
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """
    Generic repository pattern for Neo4j
    
    Provides basic CRUD operations for all entities
    """

    def __init__(self, db, model: Type[T], label: str):
        """
        Initialize repository
        
        Args:
            db: Neo4j database connection
            model: Pydantic model class
            label: Neo4j node label
        """
        self.db = db
        self.model = model
        self.label = label

    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity
        
        Args:
            data: Entity data as dict
            
        Returns:
            Created entity
        """
        query = f"""
        CREATE (n:{self.label} $props)
        SET n.created_at = datetime()
        RETURN n
        """
        result = await self.db.execute_query(query, {"props": data})
        if not result:
            raise ValueError(f"Failed to create {self.label}")
        
        node = result[0]["n"]
        logger.info(f"Created {self.label} with id={node.get('id')}")
        return self.model(**node)

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Get entity by ID
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity or None if not found
        """
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        RETURN n
        """
        result = await self.db.execute_query(query, {"id": entity_id})
        if not result:
            return None
        return self.model(**result[0]["n"])

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Get all entities with pagination
        
        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return
            
        Returns:
            List of entities
        """
        query = f"""
        MATCH (n:{self.label})
        RETURN n
        ORDER BY n.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = await self.db.execute_query(query, {"skip": skip, "limit": limit})
        return [self.model(**row["n"]) for row in result]

    async def update(self, entity_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity
        
        Args:
            entity_id: Entity ID
            updates: Fields to update
            
        Returns:
            Updated entity or None if not found
        """
        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}
        
        if not updates:
            return await self.get_by_id(entity_id)

        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        SET n += $updates
        SET n.updated_at = datetime()
        RETURN n
        """
        result = await self.db.execute_query(query, {"id": entity_id, "updates": updates})
        if not result:
            logger.warning(f"{self.label} with id={entity_id} not found for update")
            return None
        
        logger.info(f"Updated {self.label} with id={entity_id}")
        return self.model(**result[0]["n"])

    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity
        
        Args:
            entity_id: Entity ID
            
        Returns:
            True if deleted, False if not found
        """
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        DELETE n
        RETURN count(n) as deleted
        """
        result = await self.db.execute_query(query, {"id": entity_id})
        deleted = result[0]["deleted"] > 0
        
        if deleted:
            logger.info(f"Deleted {self.label} with id={entity_id}")
        else:
            logger.warning(f"{self.label} with id={entity_id} not found for deletion")
        
        return deleted

    async def exists(self, entity_id: str) -> bool:
        """
        Check if entity exists
        
        Args:
            entity_id: Entity ID
            
        Returns:
            True if exists, False otherwise
        """
        query = f"""
        MATCH (n:{self.label} {{id: $id}})
        RETURN count(n) > 0 as exists
        """
        result = await self.db.execute_query(query, {"id": entity_id})
        return result[0]["exists"]

    async def count(self) -> int:
        """
        Count all entities
        
        Returns:
            Number of entities
        """
        query = f"""
        MATCH (n:{self.label})
        RETURN count(n) as count
        """
        result = await self.db.execute_query(query)
        return result[0]["count"]
