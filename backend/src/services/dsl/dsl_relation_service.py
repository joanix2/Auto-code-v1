"""
DSLRelation Service - Business logic for relationships with ontological reasoning
"""

import logging
from typing import Any
from uuid import uuid4

from src.models.dsl.dsl_relation import (
    DSLRelation,
    DSLRelationType,
)
from src.repositories.dsl.dsl_concept_repository import DSLConceptRepository
from src.repositories.dsl.dsl_relation_repository import DSLRelationRepository
from src.services.base_service import BaseService

logger = logging.getLogger(__name__)


class DSLRelationService(BaseService[DSLRelation]):
    """
    Service for relationship operations with ontological reasoning

    Inverse Properties:
    - IS_A ↔ HAS_SUBCLASS (A is_a B → B has_subclass A)
    - HAS_PART ↔ PART_OF (A has_part B → B part_of A)
    """

    # Mapping of relationship types to their inverse types
    INVERSE_RELATIONSHIPS = {
        DSLRelationType.IS_A: DSLRelationType.HAS_SUBCLASS,
        DSLRelationType.HAS_SUBCLASS: DSLRelationType.IS_A,
        DSLRelationType.HAS_PART: DSLRelationType.PART_OF,
        DSLRelationType.PART_OF: DSLRelationType.HAS_PART,
    }

    def __init__(self, dsl_relation_repo: DSLRelationRepository, dsl_concept_repo: DSLConceptRepository):
        self.dsl_relation_repo = dsl_relation_repo
        self.dsl_concept_repo = dsl_concept_repo

    async def create(self, data: dict[str, Any]) -> DSLRelation:
        """
        Create a relationship with or without ontological reasoning

        Si les IDs source/target sont fournis dans data, crée une relation complète
        avec les edges DOMAIN/RANGE et le raisonnement ontologique.

        Sinon, crée uniquement le noeud DSLRelation sans connexions.
        Les connexions seront ajoutées via le système d'edges.

        Args:
            data: DSLRelation creation data (dict with optional source/target IDs)

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
            relationship = await self.dsl_relation_repo.create_with_concepts(relationship_data)

            logger.info(f"Created relationship: {relationship.name} with DOMAIN/RANGE connections")

            # Apply ontological reasoning - create inverse relationship
            await self._create_inverse_relationship(
                relationship, data.get("source_id"), data.get("target_id")
            )
        else:
            # Mode standalone : juste le noeud, sans connexions
            relationship = await self.dsl_relation_repo.create_standalone(relationship_data)

            logger.info(
                f"Created standalone relationship node: {relationship.name} (id={relationship.id})"
            )

        return relationship

    async def _create_inverse_relationship(
        self, relationship: DSLRelation, source_id: str, target_id: str
    ) -> DSLRelation | None:
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
        source_concept = await self.dsl_concept_repo.get_by_id(source_id)
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
            "_inverse_of": relationship.id,  # Reference to original relationship
        }

        try:
            # Check if inverse already exists
            existing_inverse = await self.dsl_relation_repo.get_between_concepts(
                target_id, source_id
            )

            if existing_inverse:
                logger.info(f"Inverse relationship already exists: {existing_inverse.id}")
                return existing_inverse

            # Create inverse relationship
            inverse_rel = await self.dsl_relation_repo.create_with_concepts(inverse_data)

            logger.info(
                f"Created inverse relationship: {inverse_type.value} with DOMAIN/RANGE connections"
            )

            return inverse_rel

        except Exception as e:
            logger.error(f"Failed to create inverse relationship: {e}")
            return None

    async def get_by_id(self, relationship_id: str) -> DSLRelation | None:
        """Get relationship by ID"""
        return await self.dsl_relation_repo.get_by_id(relationship_id)

    async def get_all(self, filters: dict[str, Any] | None = None) -> list[DSLRelation]:
        """
        Get all relationships with optional filters

        Args:
            filters: Optional filters (dsl_id, skip, limit, include_inverse)

        Returns:
            List of relationships
        """
        if not filters:
            filters = {}

        skip = filters.get("skip", 0)
        limit = filters.get("limit", 100)
        include_inverse = filters.get("include_inverse", True)

        # Filter by dsl
        if "dsl_id" in filters:
            return await self.get_by_dsl(
                filters["dsl_id"], skip, limit, include_inverse
            )

        # No filters - get all
        relationships = await self.dsl_relation_repo.get_all(skip, limit)

        if not include_inverse:
            # Filter out inverse relationships
            relationships = [r for r in relationships if not hasattr(r, "_is_inverse")]

        return relationships

    async def get_by_dsl(
        self, dsl_id: str, skip: int = 0, limit: int = 100, include_inverse: bool = True
    ) -> list[DSLRelation]:
        """
        Get all relationships for a dsl

        Args:
            dsl_id: DSLGraph ID
            skip: Number to skip
            limit: Max results
            include_inverse: Include inverse relationships

        Returns:
            List of relationships
        """
        relationships = await self.dsl_relation_repo.get_by_dsl(dsl_id, skip, limit)

        if not include_inverse:
            # Filter out inverse relationships
            relationships = [r for r in relationships if not hasattr(r, "_is_inverse")]

        return relationships

    async def get_by_concept(
        self, concept_id: str, direction: str = "both"
    ) -> dict[str, list[DSLRelation]]:
        """
        Get all relationships for a concept

        Args:
            concept_id: DSLConcept ID
            direction: "outgoing", "incoming", or "both"

        Returns:
            Dict with "outgoing" and "incoming" relationship lists
        """
        result = {"outgoing": [], "incoming": []}

        if direction in ["outgoing", "both"]:
            result["outgoing"] = await self.dsl_relation_repo.get_by_source_concept(concept_id)

        if direction in ["incoming", "both"]:
            result["incoming"] = await self.dsl_relation_repo.get_by_target_concept(concept_id)

        return result

    async def get_by_type(
        self, dsl_id: str, relationship_type: DSLRelationType
    ) -> list[DSLRelation]:
        """Get all relationships of a specific type"""
        return await self.dsl_relation_repo.get_by_type(dsl_id, relationship_type)

    async def update(
        self, relationship_id: str, update_data: dict[str, Any]
    ) -> DSLRelation | None:
        """
        Update a relationship

        Args:
            relationship_id: DSLRelation ID
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
            relationship = await self.dsl_relation_repo.update(relationship_id, updates)
        else:
            relationship = await self.dsl_relation_repo.update(relationship_id, updates)

        if relationship:
            logger.info(f"Updated relationship: {relationship_id}")

        return relationship

    async def delete(self, relationship_id: str) -> bool:
        """
        Delete a relationship

        Note: La suppression de la relation inverse n'est pas implémentée car
        les informations de source/target sont dans les edges Neo4j DOMAIN/RANGE,
        pas dans le modèle DSLRelation.

        Args:
            relationship_id: DSLRelation ID

        Returns:
            True if deleted
        """
        # Get the relationship first to verify it exists
        relationship = await self.get_by_id(relationship_id)
        if not relationship:
            return False

        # Delete the relationship
        # Note: Les edges DOMAIN/RANGE seront automatiquement supprimés par la requête Neo4j
        deleted = await self.dsl_relation_repo.delete(relationship_id)

        if deleted:
            logger.info(f"Deleted relationship: {relationship_id}")

        return deleted

    async def infer_relationships(self, dsl_id: str) -> list[DSLRelation]:
        """
        Infer new relationships based on existing ones using ontological reasoning

        Examples:
        - If A is_a B and B is_a C, then A is_a C (transitivity of is_a)
        - If A part_of B and B part_of C, then A part_of C (transitivity of part_of)

        Args:
            dsl_id: DSLGraph ID

        Returns:
            List of inferred relationships

        Note: Cette fonctionnalité nécessite d'accéder aux relations DOMAIN/RANGE depuis Neo4j.
        Elle est actuellement désactivée.
        """
        logger.warning(
            "infer_relationships is not yet implemented - requires DOMAIN/RANGE edge queries"
        )
        return []

        # TODO: Réimplémenter en utilisant des requêtes Neo4j pour récupérer les DOMAIN/RANGE edges
