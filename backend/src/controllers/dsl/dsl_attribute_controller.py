"""
DSLAttribute Controller - API endpoints for attributes
"""

import logging
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from src.database import get_db
from src.models.dsl.dsl_attribute import DSLAttribute, DSLAttributeCreate, DSLAttributeUpdate
from src.models.oauth.user import User
from src.repositories.dsl.dsl_attribute_repository import DSLAttributeRepository
from src.repositories.dsl.dsl_concept_repository import DSLConceptRepository
from src.repositories.dsl.dsl_repository import DSLRepository
from src.services.dsl.dsl_attribute_service import DSLAttributeService
from src.utils.auth import get_current_user

from ..base_controller import BaseController

logger = logging.getLogger(__name__)

# Router definition
router = APIRouter(prefix="/api/dsls/attributes", tags=["attributes"])


class DSLAttributeController(BaseController[DSLAttribute, DSLAttributeCreate, DSLAttributeUpdate]):
    """Controller for attribute CRUD operations"""

    def __init__(self, service: DSLAttributeService):
        self.service = service

    def get_resource_name(self) -> str:
        return "attribute"

    def get_resource_name_plural(self) -> str:
        return "attributes"

    async def generate_id(self, data: dict[str, Any]) -> str:
        """Generate unique ID for attribute"""
        return str(uuid4())

    async def validate_create(
        self, data: DSLAttributeCreate, current_user: User, db
    ) -> dict[str, Any]:
        """Validate attribute creation"""
        validated_data = data.model_dump()

        # DSLConcept existence is validated in service

        return validated_data

    async def validate_update(
        self, resource_id: str, updates: DSLAttributeUpdate, current_user: User, db
    ) -> dict[str, Any] | None:
        """Validate attribute update"""
        # Check if attribute exists
        attribute = await self.service.get_by_id(resource_id)
        if not attribute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DSLAttribute not found")

        return None  # No modifications needed

    async def validate_delete(self, resource_id: str, current_user: User, db) -> DSLAttribute:
        """Validate attribute deletion"""
        # Check if attribute exists
        attribute = await self.service.get_by_id(resource_id)
        if not attribute:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DSLAttribute not found")

        return attribute

    async def sync_from_github(
        self, github_token: str, current_user: User, **kwargs
    ) -> list[DSLAttribute]:
        """Sync attributes from GitHub (not implemented)"""
        return []

    # Override create to use service
    async def create(self, data: DSLAttributeCreate, current_user: User, db) -> DSLAttribute:
        """Create a new attribute"""
        try:
            validated_data = await self.validate_create(data, current_user, db)
            attribute = await self.service.create(validated_data)
            logger.info(f"Created attribute {attribute.id}")
            return attribute
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"DSLAttribute creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create attribute: {str(e)}",
            )

    # Override update to handle Pydantic model conversion
    async def update(
        self, attribute_id: str, updates: DSLAttributeUpdate, current_user: User, db
    ) -> DSLAttribute:
        """Update an attribute"""
        logger.info(f"🔍 Updating attribute {attribute_id}")

        # Convert Pydantic model to dict, excluding unset values
        update_dict = updates.model_dump(exclude_unset=True)
        logger.info(f"🔍 Update data: {update_dict}")

        updated_attribute = await self.service.update(attribute_id, update_dict)

        if not updated_attribute:
            logger.error(f"❌ service.update returned None for attribute {attribute_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DSLAttribute {attribute_id} not found"
            )

        logger.info(f"✅ Successfully updated attribute {attribute_id}")
        return updated_attribute

    # Additional methods

    async def get_by_concept(
        self, concept_id: str, skip: int = 0, limit: int = 100
    ) -> list[DSLAttribute]:
        """Get all attributes for a concept"""
        return await self.service.get_by_concept(concept_id, skip, limit)

    async def get_required_attributes(self, concept_id: str) -> list[DSLAttribute]:
        """Get all required attributes for a concept"""
        return await self.service.get_required_attributes(concept_id)


# ============================================================================
# ROUTES
# ============================================================================


def get_controller(db=Depends(get_db)) -> DSLAttributeController:
    """Factory function to create DSLAttributeController instance"""

    attribute_repo = DSLAttributeRepository(db)
    concept_repo = DSLConceptRepository(db)
    dsl_repo = DSLRepository(db)
    service = DSLAttributeService(attribute_repo, concept_repo, dsl_repo)
    return DSLAttributeController(service)


@router.get("/concept/{concept_id}", response_model=list[DSLAttribute])
async def get_attributes_by_concept(
    concept_id: str,
    skip: int = 0,
    limit: int = 100,
    controller: DSLAttributeController = Depends(get_controller),
):
    """Get all attributes for a specific concept"""
    return await controller.get_by_concept(concept_id, skip, limit)


@router.get("/dsl/{dsl_id}", response_model=list[DSLAttribute])
async def get_attributes_by_dsl(
    dsl_id: str,
    skip: int = 0,
    limit: int = 100,
    controller: DSLAttributeController = Depends(get_controller),
):
    """Get all attributes for a specific dsl"""
    attributes = await controller.service.attribute_repo.get_by_dsl(dsl_id, skip, limit)
    return attributes


@router.get("/{attribute_id}", response_model=DSLAttribute)
async def get_attribute(
    attribute_id: str, controller: DSLAttributeController = Depends(get_controller)
):
    """Get attribute by ID"""
    attribute = await controller.service.get_by_id(attribute_id)
    if not attribute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DSLAttribute not found")
    return attribute


@router.post("/", response_model=DSLAttribute, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    attribute_data: DSLAttributeCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLAttributeController = Depends(get_controller),
):
    """Create a new attribute"""
    logger.info(
        f"Creating attribute: {attribute_data.name} for concept {attribute_data.concept_id}"
    )
    return await controller.create(attribute_data, current_user, db)


@router.put("/{attribute_id}", response_model=DSLAttribute)
async def update_attribute(
    attribute_id: str,
    updates: DSLAttributeUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLAttributeController = Depends(get_controller),
):
    """Update an attribute"""
    return await controller.update(attribute_id, updates, current_user, db)


@router.delete("/{attribute_id}")
async def delete_attribute(
    attribute_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLAttributeController = Depends(get_controller),
):
    """Delete an attribute"""
    await controller.validate_delete(attribute_id, current_user, db)
    success = await controller.service.delete(attribute_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DSLAttribute not found")

    return {"message": "DSLAttribute deleted successfully"}
