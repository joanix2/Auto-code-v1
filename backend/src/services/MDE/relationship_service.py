"""
Relationship Service - Business logic for relationships with ontological reasoning
"""
from typing import Optional, List, Dict, Any
import logging
from uuid import uuid4

from src.services.base_service import BaseService
from src.repositories.MDE.relationship_repository import RelationshipRepository
from src.repositories.MDE.concept_repository import ConceptRepository
from src.models.MDE.metamodel.relationship import (
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
        
        Si source_concept_id et target_concept_id sont fournis, crée une relation complète
        avec les edges DOMAIN/RANGE et le raisonnement ontologique.
        
        Sinon, crée uniquement le noeud Relationship sans connexions.
        Les connexions seront ajoutées via le système d'edges.
        
        Args:
            data: Relationship creation data (dict)
            
        Returns:
            Created relationship
        """
        # Prepare data
        relationship_data = {**data}
        relationship_data["id"] = str(uuid4())
        
        # Vérifier si on a les connexions source/target
        has_connections = bool(data.get("source_concept_id") and data.get("target_concept_id"))
        
        if has_connections:
            # Mode complet avec DOMAIN/RANGE edges et raisonnement ontologique
            # Get target concept name if not provided
            if not relationship_data.get("target_concept_name"):
                target_concept_id = data.get("target_concept_id")
                target_concept = await self.concept_repo.get_by_id(target_concept_id)
                if target_concept:
                    relationship_data["target_concept_name"] = target_concept.name
            
            # Create the relationship with concepts
            relationship = await self.relationship_repo.create_with_concepts(relationship_data)
            
            logger.info(
                f"Created relationship: {relationship.name} "
                f"({relationship.source_concept_id} → {relationship.target_concept_id})"
            )
            
            # Apply ontological reasoning - create inverse relationship
            await self._create_inverse_relationship(relationship)
        else:
            # Mode standalone : juste le noeud, sans connexions
            relationship = await self.relationship_repo.create_standalone(relationship_data)
            
            logger.info(
                f"Created standalone relationship node: {relationship.name} "
                f"(id={relationship.id})"
            )
        
        return relationship
    
    async def _create_inverse_relationship(self, relationship: Relationship) -> Optional[Relationship]:
        """
        Create inverse relationship based on ontological reasoning
        
        Args:
            relationship: Original relationship
            
        Returns:
            Inverse relationship or None
        """
        # Get the inverse relationship type
        inverse_type = self.INVERSE_RELATIONSHIPS.get(relationship.type)
        if not inverse_type:
            logger.debug(f"No inverse relationship defined for {relationship.type}")
            return None
        
        # Get source concept name for the inverse relationship
        source_concept = await self.concept_repo.get_by_id(relationship.source_concept_id)
        if not source_concept:
            logger.warning(f"Source concept not found: {relationship.source_concept_id}")
            return None
        
        # Create inverse relationship data
        inverse_data = {
            "id": str(uuid4()),
            "type": inverse_type.value,  # Use the inverse type
            "source_concept_id": relationship.target_concept_id,
            "target_concept_id": relationship.source_concept_id,
            "target_concept_name": source_concept.name,
            "description": f"Inverse of: {relationship.description or relationship.name}",
            "metamodel_id": relationship.metamodel_id,
            "_is_inverse": True,  # Mark as inverse for potential filtering
            "_inverse_of": relationship.id  # Reference to original relationship
        }
        
        try:
            # Check if inverse already exists
            existing_inverse = await self.relationship_repo.get_between_concepts(
                relationship.target_concept_id,
                relationship.source_concept_id
            )
            
            if existing_inverse:
                logger.info(f"Inverse relationship already exists: {existing_inverse.id}")
                return existing_inverse
            
            # Create inverse relationship
            inverse_rel = await self.relationship_repo.create_with_concepts(inverse_data)
            
            logger.info(
                f"Created inverse relationship: {inverse_type.value} "
                f"({inverse_rel.source_concept_id} → {inverse_rel.target_concept_id})"
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
        Delete a relationship and its inverse
        
        Args:
            relationship_id: Relationship ID
            
        Returns:
            True if deleted
        """
        # Get the relationship first
        relationship = await self.get_by_id(relationship_id)
        if not relationship:
            return False
        
        # Try to find and delete inverse relationship
        inverse = await self.relationship_repo.get_between_concepts(
            relationship.target_concept_id,
            relationship.source_concept_id
        )
        
        if inverse:
            await self.relationship_repo.delete(inverse.id)
            logger.info(f"Deleted inverse relationship: {inverse.id}")
        
        # Delete the main relationship
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
        """
        inferred = []
        
        # Get all is_a relationships
        is_a_rels = await self.get_by_type(metamodel_id, RelationshipType.IS_A)
        
        # Apply transitivity: if A is_a B and B is_a C, then A is_a C
        for rel1 in is_a_rels:
            for rel2 in is_a_rels:
                if rel1.target_concept_id == rel2.source_concept_id:
                    # Check if A -> C relationship already exists
                    existing = await self.relationship_repo.get_between_concepts(
                        rel1.source_concept_id,
                        rel2.target_concept_id
                    )
                    
                    if not existing:
                        # Create inferred relationship
                        target_concept = await self.concept_repo.get_by_id(rel2.target_concept_id)
                        
                        inferred_data = {
                            "id": str(uuid4()),
                            "type": RelationshipType.IS_A.value,
                            "source_concept_id": rel1.source_concept_id,
                            "target_concept_id": rel2.target_concept_id,
                            "target_concept_name": target_concept.name if target_concept else None,
                            "description": f"Inferred from transitivity",
                            "metamodel_id": metamodel_id,
                            "_is_inferred": True
                        }
                        
                        inferred_rel = await self.relationship_repo.create_with_concepts(inferred_data)
                        inferred.append(inferred_rel)
                        
                        logger.info(
                            f"Inferred relationship: {inferred_rel.source_concept_id} is_a "
                            f"{inferred_rel.target_concept_id} (via {rel1.target_concept_id})"
                        )
        
        # Apply same logic for part_of relationships
        part_of_rels = await self.get_by_type(metamodel_id, RelationshipType.PART_OF)
        
        for rel1 in part_of_rels:
            for rel2 in part_of_rels:
                if rel1.target_concept_id == rel2.source_concept_id:
                    existing = await self.relationship_repo.get_between_concepts(
                        rel1.source_concept_id,
                        rel2.target_concept_id
                    )
                    
                    if not existing:
                        target_concept = await self.concept_repo.get_by_id(rel2.target_concept_id)
                        
                        inferred_data = {
                            "id": str(uuid4()),
                            "type": RelationshipType.PART_OF.value,
                            "source_concept_id": rel1.source_concept_id,
                            "target_concept_id": rel2.target_concept_id,
                            "target_concept_name": target_concept.name if target_concept else None,
                            "description": f"Inferred from transitivity",
                            "metamodel_id": metamodel_id,
                            "_is_inferred": True
                        }
                        
                        inferred_rel = await self.relationship_repo.create_with_concepts(inferred_data)
                        inferred.append(inferred_rel)
        
        logger.info(f"Inferred {len(inferred)} new relationships for metamodel {metamodel_id}")
        
        return inferred
