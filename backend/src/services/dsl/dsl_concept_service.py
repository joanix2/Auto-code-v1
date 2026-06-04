"""
DSLConcept Service - Business logic for concepts
"""

import logging
from typing import Any
from uuid import uuid4

from src.models.dsl.dsl_concept import DSLConcept
from src.repositories.dsl.dsl_concept_repository import DSLConceptRepository
from src.repositories.dsl.dsl_repository import DSLRepository
from src.services.base_service import BaseService

logger = logging.getLogger(__name__)


class DSLConceptService(BaseService[DSLConcept]):
    """Service for concept operations"""

    def __init__(self, dsl_concept_repo: DSLConceptRepository, dsl_repo: DSLRepository):
        self.dsl_concept_repo = dsl_concept_repo
        self.dsl_repo = dsl_repo

    async def create(self, data: dict[str, Any]) -> DSLConcept:
        """
        Create a concept

        Args:
            data: DSLConcept creation data (dict)

        Returns:
            Created concept
        """
        # Convert to DSLConceptCreate if needed
        if not isinstance(data, dict):
            data = data.model_dump()

        # Check if dsl exists (frontend sends graph_id)
        graph_id = data.get("graph_id")
        dsl = await self.dsl_repo.get_by_id(graph_id)
        if not dsl:
            raise ValueError(f"DSLGraph not found: {graph_id}")

        # Check for duplicate name in same dsl
        name = data.get("name")
        existing = await self.dsl_concept_repo.get_by_name(graph_id, name)
        if existing:
            raise ValueError(f"DSLConcept with name '{name}' already exists in this dsl")

        # Generate ID and create concept
        concept_data = {**data}
        concept_data["id"] = str(uuid4())

        logger.info(f"🔍 Creating concept with data: {concept_data}")

        # Create concept (repository will create HAS_CONCEPT relationship)
        concept = await self.dsl_concept_repo.create(concept_data)

        logger.info(f"Created concept: {concept.name} (id={concept.id})")

        return concept

    async def get_by_id(self, concept_id: str) -> DSLConcept | None:
        """Get concept by ID"""
        return await self.dsl_concept_repo.get_by_id(concept_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[DSLConcept]:
        """
        Get all concepts with pagination

        Args:
            skip: Number of concepts to skip
            limit: Maximum number of concepts to return

        Returns:
            List of concepts
        """
        return await self.dsl_concept_repo.get_all(skip, limit)

    async def get_by_dsl(
        self, dsl_id: str, skip: int = 0, limit: int = 100
    ) -> list[DSLConcept]:
        """Get all concepts for a dsl"""
        return await self.dsl_concept_repo.get_by_dsl(dsl_id, skip, limit)

    async def get_with_attributes(self, concept_id: str) -> dict[str, Any] | None:
        """Get concept with all its attributes"""
        return await self.dsl_concept_repo.get_with_attributes(concept_id)

    async def update(self, concept_id: str, update_data: dict[str, Any]) -> DSLConcept | None:
        """
        Update a concept

        Args:
            concept_id: DSLConcept ID
            update_data: Update data (dict)

        Returns:
            Updated concept or None
        """
        logger.info(
            f"🔍 DSLConceptService.update called with concept_id={concept_id}, update_data={update_data}"
        )

        # Check if concept exists first
        existing_concept = await self.get_by_id(concept_id)
        logger.info(f"🔍 Existing concept: {existing_concept}")

        if not existing_concept:
            logger.error(f"❌ DSLConcept {concept_id} not found in database")
            return None

        # Remove None values
        updates = {k: v for k, v in update_data.items() if v is not None}

        if not updates:
            logger.info("ℹ️ No updates provided, returning existing concept")
            return existing_concept

        # Check for duplicate name if name is being updated
        if "name" in updates:
            logger.info(f"🔍 Checking for duplicate name: {updates['name']}")
            existing = await self.dsl_concept_repo.get_by_name(
                existing_concept.graph_id, updates["name"]
            )
            if existing and existing.id != concept_id:
                raise ValueError(
                    f"DSLConcept with name '{updates['name']}' already exists in this dsl"
                )

        logger.info(f"🚀 Calling dsl_concept_repo.update with id={concept_id}, updates={updates}")
        concept = await self.dsl_concept_repo.update(concept_id, updates)

        if concept:
            logger.info(f"✅ Updated concept: {concept_id}")
        else:
            logger.error(f"❌ dsl_concept_repo.update returned None for {concept_id}")

        return concept

    async def update_position(self, concept_id: str, x: float, y: float) -> DSLConcept | None:
        """Update concept position in graph visualization"""
        return await self.dsl_concept_repo.update_position(concept_id, x, y)

    async def delete(self, concept_id: str) -> bool:
        """
        Delete a concept

        Args:
            concept_id: DSLConcept ID

        Returns:
            True if deleted
        """
        logger.info(f"🔍 DSLConceptService.delete called for concept_id={concept_id}")

        # Get concept first to get dsl_id
        concept = await self.get_by_id(concept_id)
        logger.info(f"🔍 DSLConcept found: {concept}")

        if not concept:
            logger.warning(f"⚠️ DSLConcept {concept_id} not found")
            return False

        # Delete concept (repository should handle cascade delete of attributes and relationships)
        logger.info(f"🗑️ Calling dsl_concept_repo.delete for {concept_id}")
        deleted = await self.dsl_concept_repo.delete(concept_id)
        logger.info(f"🔍 Delete result: {deleted}")

        if deleted:
            logger.info(f"✅ Deleted concept: {concept_id}")
        else:
            logger.error(f"❌ Failed to delete concept: {concept_id}")

        return deleted

    async def count_by_dsl(self, dsl_id: str) -> int:
        """Count concepts in a dsl"""
        return await self.dsl_concept_repo.count_by_dsl(dsl_id)
