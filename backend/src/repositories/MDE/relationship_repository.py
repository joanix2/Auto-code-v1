"""
Relationship Repository - Database operations for relationships between concepts
"""
from typing import Optional, List, Dict, Any
import logging

from ..base import BaseRepository, convert_neo4j_types
from src.models.MDE.metamodel.relationship import Relationship, RelationshipType

logger = logging.getLogger(__name__)


class RelationshipRepository(BaseRepository[Relationship]):
    """Repository for relationship CRUD operations"""

    def __init__(self, db):
        super().__init__(db, Relationship, "Relationship")

    def _normalize_relationship_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize relationship data to match Node model fields
        Relationship is a Node, not an Edge
        """
        normalized = {**data}
        
        # Ensure graph_id is set from metamodel_id if present
        if "metamodel_id" in normalized and "graph_id" not in normalized:
            normalized["graph_id"] = normalized["metamodel_id"]
            
        return normalized

    async def create_standalone(self, data: Dict[str, Any]) -> Relationship:
        """
        Create a relationship node without DOMAIN/RANGE connections
        
        Les connexions DOMAIN/RANGE seront créées séparément via le système d'edges.
        Cette méthode crée uniquement le noeud Relationship.
        
        Structure in Neo4j:
        (Metamodel)-[:HAS_RELATION]->(Relationship:Node)
        
        Args:
            data: Relationship data including name, type, description
            
        Returns:
            Created relationship
        """
        metamodel_id = data.get("metamodel_id")
        name = data.get("name")
        
        if not metamodel_id:
            raise ValueError("metamodel_id is required")
        if not name:
            raise ValueError("name is required")

        # Prepare relationship node data
        rel_data = {
            "id": data.get("id"),
            "name": name,
            "type": data.get("type"),
            "description": data.get("description"),
            "graph_id": metamodel_id,
            "x_position": data.get("x_position"),
            "y_position": data.get("y_position"),
        }

        # Create Relationship node
        query = """
        MATCH (metamodel:Metamodel {id: $metamodel_id})
        CREATE (r:Relationship $props)
        SET r.created_at = datetime()
        CREATE (metamodel)-[:HAS_RELATION]->(r)
        RETURN r
        """
        result = self.db.execute_query(
            query, 
            {
                "metamodel_id": metamodel_id,
                "props": rel_data
            }
        )
        if not result:
            raise ValueError("Failed to create Relationship")
        
        node = convert_neo4j_types(result[0]["r"])
        logger.info(f"Created standalone Relationship '{node.get('name')}' (id={node.get('id')})")
        return self.model(**self._normalize_relationship_data(node))

    async def create_with_concepts(self, data: Dict[str, Any]) -> Relationship:
        """
        Create a relationship node and link it with DOMAIN and RANGE edges
        
        Structure in Neo4j:
        (Metamodel)-[:HAS_RELATION]->(Relationship:Node)
        (Relationship)-[:DOMAIN]->(SourceConcept)
        (Relationship)-[:RANGE]->(TargetConcept)
        
        Args:
            data: Relationship data with source_id and target_id in the dict
            
        Returns:
            Created relationship
        """
        metamodel_id = data.get("metamodel_id")
        name = data.get("name")
        # Ces IDs viennent du dict data, pas du modèle Relationship
        source_id = data.get("source_id")
        target_id = data.get("target_id")

        if not source_id or not target_id:
            raise ValueError("source_id and target_id are required in data dict")
        
        # Prepare relationship data (it's a Node, not an Edge)
        rel_data = {
            "id": data.get("id"),
            "name": name,
            "type": data.get("type"),
            "description": data.get("description"),
            "graph_id": metamodel_id,
            "x_position": data.get("x_position"),
            "y_position": data.get("y_position"),
        }

        # Create Relationship node with DOMAIN and RANGE edges
        query = """
        MATCH (metamodel:Metamodel {id: $metamodel_id})
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        CREATE (r:Relationship $props)
        SET r.created_at = datetime()
        CREATE (metamodel)-[:HAS_RELATION]->(r)
        CREATE (r)-[:DOMAIN]->(source)
        CREATE (r)-[:RANGE]->(target)
        RETURN r
        """
        result = self.db.execute_query(
            query, 
            {
                "metamodel_id": metamodel_id,
                "source_id": source_id, 
                "target_id": target_id, 
                "props": rel_data
            }
        )
        if not result:
            raise ValueError("Failed to create Relationship")
        
        node = convert_neo4j_types(result[0]["r"])
        logger.info(f"Created Relationship '{node.get('name')}' (id={node.get('id')}) with DOMAIN/RANGE edges")
        return self.model(**self._normalize_relationship_data(node))

    async def get_by_metamodel(self, metamodel_id: str, skip: int = 0, limit: int = 100) -> List[Relationship]:
        """
        Get all relationships for a specific metamodel via HAS_RELATION edge
        
        Args:
            metamodel_id: Metamodel ID
            skip: Number to skip
            limit: Max results
            
        Returns:
            List of relationships
        """
        query = """
        MATCH (m:Metamodel {id: $metamodel_id})-[:HAS_RELATION]->(r:Relationship)
        OPTIONAL MATCH (r)-[:DOMAIN]->(source:Concept)
        OPTIONAL MATCH (r)-[:RANGE]->(target:Concept)
        RETURN r, source.id as source_id, source.name as source_name, 
               target.id as target_id, target.name as target_name
        ORDER BY r.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "skip": skip, "limit": limit})
        
        relationships = []
        for row in result:
            rel_data = convert_neo4j_types(row["r"])
            # Add source and target info from the graph edges
            rel_data["source_id"] = row["source_id"]
            rel_data["source_label"] = row["source_name"]
            rel_data["target_id"] = row["target_id"]
            rel_data["target_label"] = row["target_name"]
            rel_data["graph_id"] = metamodel_id
            
            relationships.append(self.model(**self._normalize_relationship_data(rel_data)))
        
        return relationships

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
        MATCH (m:Metamodel {id: $metamodel_id})-[:HAS_RELATION]->(r:Relationship {type: $type})
        OPTIONAL MATCH (r)-[:DOMAIN]->(source:Concept)
        OPTIONAL MATCH (r)-[:RANGE]->(target:Concept)
        RETURN r, source.id as source_id, source.name as source_name,
               target.id as target_id, target.name as target_name
        ORDER BY r.created_at ASC
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id, "type": relationship_type.value})
        
        relationships = []
        for row in result:
            rel_data = convert_neo4j_types(row["r"])
            rel_data["source_id"] = row["source_id"]
            rel_data["source_label"] = row["source_name"]
            rel_data["target_id"] = row["target_id"]
            rel_data["target_label"] = row["target_name"]
            rel_data["graph_id"] = metamodel_id
            relationships.append(self.model(**self._normalize_relationship_data(rel_data)))
        
        return relationships

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
        MATCH (r:Relationship)-[:DOMAIN]->(source:Concept {id: $source_id})
        MATCH (r)-[:RANGE]->(target:Concept {id: $target_id})
        RETURN r, source.id as source_id, source.name as source_name,
               target.id as target_id, target.name as target_name
        """
        result = self.db.execute_query(query, {"source_id": source_id, "target_id": target_id})
        if not result:
            return None
        
        rel_data = convert_neo4j_types(result[0]["r"])
        rel_data["source_id"] = result[0]["source_id"]
        rel_data["source_label"] = result[0]["source_name"]
        rel_data["target_id"] = result[0]["target_id"]
        rel_data["target_label"] = result[0]["target_name"]
        
        return self.model(**self._normalize_relationship_data(rel_data))

    async def count_by_metamodel(self, metamodel_id: str) -> int:
        """
        Count relationships in a metamodel via HAS_RELATION edge
        
        Args:
            metamodel_id: Metamodel ID
            
        Returns:
            Number of relationships
        """
        query = """
        MATCH (m:Metamodel {id: $metamodel_id})-[:HAS_RELATION]->(r:Relationship)
        RETURN count(r) as count
        """
        result = self.db.execute_query(query, {"metamodel_id": metamodel_id})
        return result[0]["count"] if result else 0

    async def delete(self, entity_id: str) -> bool:
        """
        Delete a relationship and its DOMAIN, RANGE, and HAS_RELATION edges
        
        Args:
            entity_id: Relationship ID
            
        Returns:
            True if deleted, False if not found
        """
        query = """
        MATCH (r:Relationship {id: $id})
        OPTIONAL MATCH (m:Metamodel)-[has:HAS_RELATION]->(r)
        OPTIONAL MATCH (r)-[domain:DOMAIN]->()
        OPTIONAL MATCH (r)-[range:RANGE]->()
        WITH r, has, domain, range, count(r) as node_count
        DELETE has, domain, range, r
        RETURN node_count as deleted
        """
        result = self.db.execute_query(query, {"id": entity_id})
        deleted = result and len(result) > 0 and result[0]["deleted"] > 0
        
        if deleted:
            logger.info(f"🗑️ Deleted Relationship with id={entity_id} and its edges (DOMAIN, RANGE, HAS_RELATION)")
        else:
            logger.warning(f"⚠️ Relationship with id={entity_id} not found for deletion")
        
        return deleted
