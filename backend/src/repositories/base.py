"""
Base repository with generic CRUD operations
"""
from typing import TypeVar, Generic, Optional, List, Type, Dict, Any
from pydantic import BaseModel
from abc import ABC
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


def prepare_neo4j_properties(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare data for Neo4j by converting complex types to JSON strings
    
    Neo4j properties can only be:
    - Primitives: str, int, float, bool
    - Lists of primitives
    - None
    
    Complex types (dict, list of dicts) must be serialized to JSON strings.
    
    Args:
        data: Dictionary with potentially complex types
        
    Returns:
        Dictionary with Neo4j-compatible types
    """
    prepared = {}
    for key, value in data.items():
        if value is None:
            prepared[key] = None
        elif isinstance(value, (str, int, float, bool)):
            # Primitive types are OK
            prepared[key] = value
        elif isinstance(value, list):
            # Check if it's a list of primitives
            if all(isinstance(item, (str, int, float, bool)) for item in value):
                prepared[key] = value
            else:
                # List of complex objects - serialize to JSON
                prepared[key] = json.dumps(value)
        elif isinstance(value, dict):
            # Dict - serialize to JSON string
            prepared[key] = json.dumps(value)
        else:
            # Other types - convert to string
            logger.warning(f"Converting non-standard type {type(value)} to string for key '{key}'")
            prepared[key] = str(value)
    
    return prepared


def convert_neo4j_types(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Neo4j types to Python native types
    Also deserializes JSON strings back to dicts/lists.
    Also handles backward compatibility for field name changes.
    
    Args:
        node: Node data from Neo4j
        
    Returns:
        Dict with converted types
    """
    from neo4j.time import DateTime as Neo4jDateTime
    
    converted = {}
    for key, value in node.items():
        if isinstance(value, Neo4jDateTime):
            # Convert Neo4j DateTime to Python datetime
            converted[key] = datetime(
                value.year, value.month, value.day,
                value.hour, value.minute, value.second,
                value.nanosecond // 1000  # Convert nanoseconds to microseconds
            )
        elif isinstance(value, str):
            # Try to deserialize JSON strings (for settings, metadata, tags, etc.)
            if value.startswith('{') or value.startswith('['):
                try:
                    converted[key] = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    # Not JSON, keep as string
                    converted[key] = value
            else:
                converted[key] = value
        else:
            converted[key] = value
    
    # Backward compatibility: map old field names to new ones
    # For concepts that still have old field names in Neo4j
    if 'metamodel_id' in converted and 'graph_id' not in converted:
        converted['graph_id'] = converted['metamodel_id']
    if 'x' in converted and 'x_position' not in converted:
        converted['x_position'] = converted['x']
    if 'y' in converted and 'y_position' not in converted:
        converted['y_position'] = converted['y']
    
    return converted


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
        # Debug: log what we're sending to Neo4j
        logger.info(f"🔍 BaseRepository.create data keys: {list(data.keys())}")
        logger.info(f"🔍 BaseRepository.create data: {data}")
        
        # Prepare data for Neo4j (convert complex types to JSON strings)
        prepared_data = prepare_neo4j_properties(data)
        logger.info(f"🔍 Prepared data for Neo4j: {prepared_data}")
        
        query = f"""
        CREATE (n:{self.label} $props)
        SET n.created_at = datetime()
        RETURN n
        """
        result = self.db.execute_query(query, {"props": prepared_data})
        if not result:
            raise ValueError(f"Failed to create {self.label}")
        
        node = convert_neo4j_types(result[0]["n"])
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
        result = self.db.execute_query(query, {"id": entity_id})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["n"]))

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
        result = self.db.execute_query(query, {"skip": skip, "limit": limit})
        return [self.model(**convert_neo4j_types(row["n"])) for row in result]

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
        logger.info(f"🔍 Executing update query for {self.label} id={entity_id}, updates={updates}")
        result = self.db.execute_query(query, {"id": entity_id, "updates": updates})
        logger.info(f"🔍 Update query result: {result}")
        
        if not result:
            logger.warning(f"{self.label} with id={entity_id} not found for update")
            return None
        
        logger.info(f"Updated {self.label} with id={entity_id}")
        return self.model(**convert_neo4j_types(result[0]["n"]))

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
        result = self.db.execute_query(query, {"id": entity_id})
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
