"""
Relationship Service - Business logic for relationships with ontological reasoning
"""
from typing import Optional, List, Dict, Any
import logging
from uuid import uuid4

from src.services.base_service import BaseService
from src.repositories.MDE.relationship_repository import RelationshipRepository
from src.repositories.MDE.concept_repository import ConceptRepository
from src.models.MDE.M2.relationship import (
    Relationship,
    RelationshipType,
    RelationshipCreate,
    RelationshipUpdate
)

logger = logging.getLogger(__name__)


class RelationshipService(BaseService[Relationship]):
    """
    Service for relationship operations with ontological reasoning
    
    Inverse Properties:
    - IS_A ↔ HAS_SUBCLASS (A is_a B → B has_subclass A)
    - HAS_PART ↔ PART_OF (A has_part B → B part_of A)
    """
    
    # Mapping of relationship types to their inverse types
    INVERSE_RELATIONSHIPS = {
        RelationshipType.IS_A: RelationshipType.HAS_SUBCLASS,
        RelationshipType.HAS_SUBCLASS: RelationshipType.IS_A,
        RelationshipType.HAS_PART: RelationshipType.PART_OF,
        RelationshipType.PART_OF: RelationshipType.HAS_PART,
    }
    
    def __init__(self, relationship_repo: RelationshipRepository, concept_repo: ConceptRepository):
        self.relationship_repo = relationship_repo
        self.concept_repo = concept_repo
    
    async def create(self, data: Dict[str, Any]) -> Relationship:
        """
        Create a relationship with or without ontological reasoning
        
        Si les IDs source/target sont fournis dans data, crée une relation complète
        avec les edges DOMAIN/RANGE et le raisonnement ontologique.
        
        Sinon, crée uniquement le noeud Relationship sans connexions.
        Les connexions seront ajoutées via le système d'edges.
        
        Args:
            data: Relationship creation data (dict with optional source/target IDs)
            
        Returns:
            Created relationship
        """
        # Prepare data
        relationship_data = {**data}
        relationship_data["id"] = str(uuid4())
        
        # Vérifier si on a les connexions source/target dans le dict data
        has_connections = bool(data.get("source_id") and data.get("target_id"))
        
        if has_connections:
            # Mode complet avec DOMAIN/RANGE edges et raisonnement ontologique
            # Create the relationship with concepts
            relationship = await self.relationship_repo.create_with_concepts(relationship_data)
            
            logger.info(
                f"Created relationship: {relationship.name} with DOMAIN/RANGE connections"
            )
            
            # Apply ontological reasoning - create inverse relationship
            await self._create_inverse_relationship(relationship, data.get("source_id"), data.get("target_id"))
        else:
            # Mode standalone : juste le noeud, sans connexions
            relationship = await self.relationship_repo.create_standalone(relationship_data)
            
            logger.info(
                f"Created standalone relationship node: {relationship.name} "
                f"(id={relationship.id})"
            )
        
        return relationship
    
    async def _create_inverse_relationship(self, relationship: Relationship, source_id: str, target_id: str) -> Optional[Relationship]:
        """
        Create inverse relationship based on ontological reasoning
        
        Args:
            relationship: Original relationship
            source_id: Source concept ID from data dict
            target_id: Target concept ID from data dict
            
        Returns:
            Inverse relationship or None
        """
        # Get the inverse relationship type
        inverse_type = self.INVERSE_RELATIONSHIPS.get(relationship.type)
        if not inverse_type:
            logger.debug(f"No inverse relationship defined for {relationship.type}")
            return None
        
        # Get source concept name for the inverse relationship
        source_concept = await self.concept_repo.get_by_id(source_id)
        if not source_concept:
            logger.warning(f"Source concept not found: {source_id}")
            return None
        
        # Create inverse relationship data
        inverse_data = {
            "id": str(uuid4()),
            "type": inverse_type.value,  # Use the inverse type
            "source_id": target_id,
            "target_id": source_id,
            "description": f"Inverse of: {relationship.description or relationship.name}",
            "graph_id": relationship.graph_id,
            "_is_inverse": True,  # Mark as inverse for potential filtering
            "_inverse_of": relationship.id  # Reference to original relationship
        }
        
        try:
            # Check if inverse already exists
            existing_inverse = await self.relationship_repo.get_between_concepts(
                target_id,
                source_id
            )
            
            if existing_inverse:
                logger.info(f"Inverse relationship already exists: {existing_inverse.id}")
                return existing_inverse
            
            # Create inverse relationship
            inverse_rel = await self.relationship_repo.create_with_concepts(inverse_data)
            
            logger.info(
                f"Created inverse relationship: {inverse_type.value} with DOMAIN/RANGE connections"
            )
            
            return inverse_rel
            
        except Exception as e:
            logger.error(f"Failed to create inverse relationship: {e}")
            return None
    
    async def get_by_id(self, relationship_id: str) -> Optional[Relationship]:
        """Get relationship by ID"""
        return await self.relationship_repo.get_by_id(relationship_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Relationship]:
        """
        Get all relationships with optional filters
        
        Args:
            filters: Optional filters (metamodel_id, skip, limit, include_inverse)
            
        Returns:
            List of relationships
        """
        if not filters:
            filters = {}
        
        skip = filters.get("skip", 0)
        limit = filters.get("limit", 100)
        include_inverse = filters.get("include_inverse", True)
        
        # Filter by metamodel
        if "metamodel_id" in filters:
            return await self.get_by_metamodel(
                filters["metamodel_id"],
                skip,
                limit,
                include_inverse
            )
        
        # No filters - get all
        relationships = await self.relationship_repo.get_all(skip, limit)
        
        if not include_inverse:
            # Filter out inverse relationships
            relationships = [r for r in relationships if not hasattr(r, "_is_inverse")]
        
        return relationships
    
    async def get_by_metamodel(
        self,
        metamodel_id: str,
        skip: int = 0,
        limit: int = 100,
        include_inverse: bool = True
    ) -> List[Relationship]:
        """
        Get all relationships for a metamodel
        
        Args:
            metamodel_id: Metamodel ID
            skip: Number to skip
            limit: Max results
            include_inverse: Include inverse relationships
            
        Returns:
            List of relationships
        """
        relationships = await self.relationship_repo.get_by_metamodel(metamodel_id, skip, limit)
        
        if not include_inverse:
            # Filter out inverse relationships
            relationships = [r for r in relationships if not hasattr(r, "_is_inverse")]
        
        return relationships
    
    async def get_by_concept(
        self,
        concept_id: str,
        direction: str = "both"
    ) -> Dict[str, List[Relationship]]:
        """
        Get all relationships for a concept
        
        Args:
            concept_id: Concept ID
            direction: "outgoing", "incoming", or "both"
            
        Returns:
            Dict with "outgoing" and "incoming" relationship lists
        """
        result = {"outgoing": [], "incoming": []}
        
        if direction in ["outgoing", "both"]:
            result["outgoing"] = await self.relationship_repo.get_by_source_concept(concept_id)
        
        if direction in ["incoming", "both"]:
            result["incoming"] = await self.relationship_repo.get_by_target_concept(concept_id)
        
        return result
    
    async def get_by_type(
        self,
        metamodel_id: str,
        relationship_type: RelationshipType
    ) -> List[Relationship]:
        """Get all relationships of a specific type"""
        return await self.relationship_repo.get_by_type(metamodel_id, relationship_type)
    
    async def update(self, relationship_id: str, update_data: Dict[str, Any]) -> Optional[Relationship]:
        """
        Update a relationship
        
        Args:
            relationship_id: Relationship ID
            update_data: Update data (dict)
            
        Returns:
            Updated relationship or None
        """
        # Remove None values
        updates = {k: v for k, v in update_data.items() if v is not None}
        
        if not updates:
            return await self.get_by_id(relationship_id)
        
        # Update target concept name if needed
        if "target_concept_name" in updates:
            relationship = await self.relationship_repo.update(relationship_id, updates)
        else:
            relationship = await self.relationship_repo.update(relationship_id, updates)
        
        if relationship:
            logger.info(f"Updated relationship: {relationship_id}")
        
        return relationship
    
    async def delete(self, relationship_id: str) -> bool:
        """
        Delete a relationship
        
        Note: La suppression de la relation inverse n'est pas implémentée car
        les informations de source/target sont dans les edges Neo4j DOMAIN/RANGE,
        pas dans le modèle Relationship.
        
        Args:
            relationship_id: Relationship ID
            
        Returns:
            True if deleted
        """
        # Get the relationship first to verify it exists
        relationship = await self.get_by_id(relationship_id)
        if not relationship:
            return False
        
        # Delete the relationship
        # Note: Les edges DOMAIN/RANGE seront automatiquement supprimés par la requête Neo4j
        deleted = await self.relationship_repo.delete(relationship_id)
        
        if deleted:
            logger.info(f"Deleted relationship: {relationship_id}")
        
        return deleted
    
    async def infer_relationships(self, metamodel_id: str) -> List[Relationship]:
        """
        Infer new relationships based on existing ones using ontological reasoning
        
        Examples:
        - If A is_a B and B is_a C, then A is_a C (transitivity of is_a)
        - If A part_of B and B part_of C, then A part_of C (transitivity of part_of)
        
        Args:
            metamodel_id: Metamodel ID
            
        Returns:
            List of inferred relationships
            
        Note: Cette fonctionnalité nécessite d'accéder aux relations DOMAIN/RANGE depuis Neo4j.
        Elle est actuellement désactivée.
        """
        logger.warning("infer_relationships is not yet implemented - requires DOMAIN/RANGE edge queries")
        return []
        
        # TODO: Réimplémenter en utilisant des requêtes Neo4j pour récupérer les DOMAIN/RANGE edges
