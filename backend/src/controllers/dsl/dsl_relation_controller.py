"""
DSLRelation Controller - API endpoints for relationships with ontological reasoning
"""

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from src.database import get_db
from src.models.dsl.dsl_relation import (
    DSLRelation,
    DSLRelationCreate,
    DSLRelationType,
    DSLRelationUpdate,
)
from src.models.oauth.user import User
from src.services.dsl.dsl_relation_service import DSLRelationService
from src.utils.auth import get_current_user

from ..base_controller import BaseController

logger = logging.getLogger(__name__)

# Router definition
router = APIRouter(prefix="/api/dsls/relations", tags=["relationships"])


class DSLRelationController(BaseController[DSLRelation, DSLRelationCreate, DSLRelationUpdate]):
    """Controller for relationship CRUD operations with ontological reasoning"""

    def __init__(self, service: DSLRelationService):
        self.service = service

    def get_resource_name(self) -> str:
        return "relationship"

    def get_resource_name_plural(self) -> str:
        return "relationships"

    async def generate_id(self, data: dict[str, Any]) -> str:
        """Generate unique ID for relationship"""
        return str(uuid4())

    async def validate_create(
        self, data: DSLRelationCreate, current_user: User, db
    ) -> dict[str, Any]:
        """Validate relationship creation"""
        validated_data = data.model_dump()

        # DSLConcepts existence is validated in service

        return validated_data

    async def validate_update(
        self, resource_id: str, updates: DSLRelationUpdate, current_user: User, db
    ) -> dict[str, Any] | None:
        """Validate relationship update"""
        # Check if relationship exists
        relationship = await self.service.get_by_id(resource_id)
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="DSLRelation not found"
            )

        # Return the update data as dict
        return updates.model_dump(exclude_unset=True)

    async def validate_delete(self, resource_id: str, current_user: User, db) -> DSLRelation:
        """Validate relationship deletion"""
        # Check if relationship exists
        relationship = await self.service.get_by_id(resource_id)
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="DSLRelation not found"
            )

        return relationship

    async def sync_from_github(
        self, github_token: str, current_user: User, **kwargs
    ) -> list[DSLRelation]:
        """Sync relationships from GitHub (not implemented)"""
        return []

    # Override create to use service with ontological reasoning
    async def create(self, data: DSLRelationCreate, current_user: User, db) -> DSLRelation:
        """
        Create a new relationship with automatic inverse creation

        When you create a relationship like "Car is_a Vehicle",
        the service automatically creates the inverse "Vehicle has_subclass Car"
        """
        try:
            validated_data = await self.validate_create(data, current_user, db)
            relationship = await self.service.create(validated_data)
            logger.info(
                f"Created relationship {relationship.id} with ontological reasoning "
                f"(inverse automatically created)"
            )
            return relationship
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DSLRelation creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create relationship: {str(e)}",
            )

    # Additional methods

    async def get_by_dsl(
        self, dsl_id: str, skip: int = 0, limit: int = 100, include_inverse: bool = True
    ) -> list[DSLRelation]:
        """Get all relationships for a dsl"""
        return await self.service.get_by_dsl(dsl_id, skip, limit, include_inverse)

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
        if direction not in ["outgoing", "incoming", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direction must be 'outgoing', 'incoming', or 'both'",
            )

        return await self.service.get_by_concept(concept_id, direction)

    async def get_by_type(
        self, dsl_id: str, relationship_type: DSLRelationType
    ) -> list[DSLRelation]:
        """Get all relationships of a specific type"""
        return await self.service.get_by_type(dsl_id, relationship_type)

    async def infer_relationships(
        self, dsl_id: str, current_user: User, db
    ) -> dict[str, Any]:
        """
        Infer new relationships using ontological reasoning

        Applies transitivity rules:
        - If A is_a B and B is_a C, then A is_a C
        - If A part_of B and B part_of C, then A part_of C

        Returns:
            Dict with count and list of inferred relationships
        """
        try:
            inferred = await self.service.infer_relationships(dsl_id)
            logger.info(f"Inferred {len(inferred)} relationships for dsl {dsl_id}")
            return {
                "count": len(inferred),
                "relationships": inferred,
                "message": f"Successfully inferred {len(inferred)} new relationships",
            }
        except Exception as e:
            logger.error(f"DSLRelation inference error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to infer relationships: {str(e)}",
            )


# ============================================================================
# ROUTES
# ============================================================================


def get_controller(db=Depends(get_db)) -> DSLRelationController:
    """Factory function to create DSLRelationController instance"""
    from src.repositories.dsl.dsl_concept_repository import DSLConceptRepository
    from src.repositories.dsl.dsl_relation_repository import DSLRelationRepository

    relationship_repo = DSLRelationRepository(db)
    concept_repo = DSLConceptRepository(db)
    service = DSLRelationService(relationship_repo, concept_repo)
    return DSLRelationController(service)


@router.get("/dsl/{dsl_id}", response_model=list[DSLRelation])
async def get_relationships_by_dsl(
    dsl_id: str,
    skip: int = 0,
    limit: int = 100,
    include_inverse: bool = True,
    controller: DSLRelationController = Depends(get_controller),
):
    """Get all relationships for a specific dsl"""
    return await controller.get_by_dsl(dsl_id, skip, limit, include_inverse)


@router.get("/concept/{concept_id}")
async def get_relationships_by_concept(
    concept_id: str,
    direction: str = "both",
    controller: DSLRelationController = Depends(get_controller),
):
    """Get all relationships for a specific concept"""
    return await controller.get_by_concept(concept_id, direction)


@router.get("/{relationship_id}", response_model=DSLRelation)
async def get_relationship(
    relationship_id: str, controller: DSLRelationController = Depends(get_controller)
):
    """Get relationship by ID"""
    relationship = await controller.service.get_by_id(relationship_id)
    if not relationship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DSLRelation not found")
    return relationship


@router.post("/", response_model=DSLRelation, status_code=status.HTTP_201_CREATED)
async def create_relationship(
    relationship_data: DSLRelationCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLRelationController = Depends(get_controller),
):
    """Create a new relationship (automatically creates inverse)"""
    return await controller.create(relationship_data, current_user, db)


@router.put("/{relationship_id}", response_model=DSLRelation)
async def update_relationship(
    relationship_id: str,
    updates: DSLRelationUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLRelationController = Depends(get_controller),
):
    """Update a relationship"""
    validated_updates = await controller.validate_update(relationship_id, updates, current_user, db)
    if validated_updates:
        return await controller.service.update(relationship_id, validated_updates)

    # If no updates, return current relationship
    relationship = await controller.service.get_by_id(relationship_id)
    if not relationship:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DSLRelation not found")
    return relationship


@router.delete("/{relationship_id}")
async def delete_relationship(
    relationship_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLRelationController = Depends(get_controller),
):
    """Delete a relationship"""
    await controller.validate_delete(relationship_id, current_user, db)
    success = await controller.service.delete(relationship_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DSLRelation not found")

    return {"message": "DSLRelation deleted successfully"}


@router.post("/dsl/{dsl_id}/infer")
async def infer_relationships(
    dsl_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLRelationController = Depends(get_controller),
):
    """Infer new relationships using ontological reasoning"""
    return await controller.infer_relationships(dsl_id, current_user, db)
