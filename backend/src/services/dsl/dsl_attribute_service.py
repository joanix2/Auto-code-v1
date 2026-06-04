"""
DSLAttribute Service - Business logic for attributes
"""

import logging
from typing import Any
from uuid import uuid4

from src.models.dsl.dsl_attribute import DSLAttribute
from src.repositories.dsl.dsl_attribute_repository import DSLAttributeRepository
from src.repositories.dsl.dsl_concept_repository import DSLConceptRepository
from src.services.base_service import BaseService

logger = logging.getLogger(__name__)


class DSLAttributeService(BaseService[DSLAttribute]):
    """Service for attribute operations"""

    def __init__(
        self,
        dsl_attribute_repo: DSLAttributeRepository,
        dsl_concept_repo: DSLConceptRepository,
        dsl_repo=None,  # Optional for backward compatibility
    ):
        self.dsl_attribute_repo = dsl_attribute_repo
        self.dsl_concept_repo = dsl_concept_repo
        self.dsl_repo = dsl_repo

    async def create(self, data: dict[str, Any]) -> DSLAttribute:
        """
        Create an attribute

        Args:
            data: DSLAttribute creation data (dict)

        Returns:
            Created attribute
        """
        # Check if concept exists (if concept_id is provided)
        concept_id = data.get("concept_id")
        if concept_id:
            concept = await self.dsl_concept_repo.get_by_id(concept_id)
            if not concept:
                raise ValueError(f"DSLConcept not found: {concept_id}")

            # Check for duplicate name in same concept
            name = data.get("name")
            existing = await self.dsl_attribute_repo.get_by_name(concept_id, name)
            if existing:
                raise ValueError(f"DSLAttribute with name '{name}' already exists in this concept")

        # Prepare data
        attribute_data = {**data}
        attribute_data["id"] = str(uuid4())

        # Create attribute (with or without relationship to concept)
        if concept_id:
            attribute = await self.dsl_attribute_repo.create_with_relationship(attribute_data)
        else:
            # Create standalone attribute
            attribute = await self.dsl_attribute_repo.create(attribute_data)

        logger.info(f"Created attribute: {attribute.name} for concept {concept_id}")

        return attribute

    async def get_by_id(self, attribute_id: str) -> DSLAttribute | None:
        """Get attribute by ID"""
        return await self.dsl_attribute_repo.get_by_id(attribute_id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[DSLAttribute]:
        """
        Get all attributes with pagination

        Args:
            skip: Number of attributes to skip
            limit: Maximum number of attributes to return

        Returns:
            List of attributes
        """
        return await self.dsl_attribute_repo.get_all(skip, limit)

    async def get_by_concept(
        self, concept_id: str, skip: int = 0, limit: int = 100
    ) -> list[DSLAttribute]:
        """Get all attributes for a concept"""
        return await self.dsl_attribute_repo.get_by_concept(concept_id, skip, limit)

    async def get_required_attributes(self, concept_id: str) -> list[DSLAttribute]:
        """Get all required attributes for a concept"""
        return await self.dsl_attribute_repo.get_required_attributes(concept_id)

    async def update(self, attribute_id: str, update_data: dict[str, Any]) -> DSLAttribute | None:
        """
        Update an attribute

        Args:
            attribute_id: DSLAttribute ID
            update_data: Update data (dict)

        Returns:
            Updated attribute or None
        """
        # Remove None values
        updates = {k: v for k, v in update_data.items() if v is not None}

        if not updates:
            return await self.get_by_id(attribute_id)

        # Check for duplicate name if name is being updated
        if "name" in updates:
            attribute = await self.get_by_id(attribute_id)
            if attribute:
                existing = await self.dsl_attribute_repo.get_by_name(
                    attribute.concept_id, updates["name"]
                )
                if existing and existing.id != attribute_id:
                    raise ValueError(
                        f"DSLAttribute with name '{updates['name']}' already exists in this concept"
                    )

        attribute = await self.dsl_attribute_repo.update(attribute_id, updates)

        if attribute:
            logger.info(f"Updated attribute: {attribute_id}")

        return attribute

    async def delete(self, attribute_id: str) -> bool:
        """
        Delete an attribute

        Args:
            attribute_id: DSLAttribute ID

        Returns:
            True if deleted
        """
        deleted = await self.dsl_attribute_repo.delete(attribute_id)

        if deleted:
            logger.info(f"Deleted attribute: {attribute_id}")

        return deleted

    async def count_by_concept(self, concept_id: str) -> int:
        """Count attributes for a concept"""
        return await self.dsl_attribute_repo.count_by_concept(concept_id)
