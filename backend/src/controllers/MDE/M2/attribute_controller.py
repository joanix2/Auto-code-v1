"""
Attribute Controller - API endpoints for attributes
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
import logging
from uuid import uuid4

from ..base_controller import BaseController
from src.services.MDE.attribute_service import AttributeService
from src.models.MDE.M2.attribute import Attribute, AttributeCreate, AttributeUpdate
from src.models.user import User
from src.database import get_db
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

# Router definition
router = APIRouter(prefix="/api/attributes", tags=["attributes"])


class AttributeController(BaseController[Attribute, AttributeCreate, AttributeUpdate]):
    """Controller for attribute CRUD operations"""
    
    def __init__(self, service: AttributeService):
        self.service = service
    
    def get_resource_name(self) -> str:
        return "attribute"
    
    def get_resource_name_plural(self) -> str:
        return "attributes"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        """Generate unique ID for attribute"""
        return str(uuid4())
    
    async def validate_create(self, data: AttributeCreate, current_user: User, db) -> Dict[str, Any]:
        """Validate attribute creation"""
        validated_data = data.model_dump()
        
        # Concept existence is validated in service
        
        return validated_data
    
    async def validate_update(
        self,
        resource_id: str,
        updates: AttributeUpdate,
        current_user: User,
        db
    ) -> Optional[Dict[str, Any]]:
        """Validate attribute update"""
        # Check if attribute exists
        attribute = await self.service.get_by_id(resource_id)
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute not found"
            )
        
        return None  # No modifications needed
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Attribute:
        """Validate attribute deletion"""
        # Check if attribute exists
        attribute = await self.service.get_by_id(resource_id)
        if not attribute:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attribute not found"
            )
        
        return attribute
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Attribute]:
        """Sync attributes from GitHub (not implemented)"""
        return []
    
    # Override create to use service
    async def create(self, data: AttributeCreate, current_user: User, db) -> Attribute:
        """Create a new attribute"""
        try:
            validated_data = await self.validate_create(data, current_user, db)
            attribute = await self.service.create(validated_data)
            logger.info(f"Created attribute {attribute.id}")
            return attribute
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Attribute creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create attribute: {str(e)}"
            )
    
    # Override update to handle Pydantic model conversion
    async def update(self, attribute_id: str, updates: AttributeUpdate, current_user: User, db) -> Attribute:
        """Update an attribute"""
        logger.info(f"🔍 Updating attribute {attribute_id}")
        
        # Convert Pydantic model to dict, excluding unset values
        update_dict = updates.model_dump(exclude_unset=True)
        logger.info(f"🔍 Update data: {update_dict}")
        
        updated_attribute = await self.service.update(attribute_id, update_dict)
        
        if not updated_attribute:
            logger.error(f"❌ service.update returned None for attribute {attribute_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attribute {attribute_id} not found"
            )
        
        logger.info(f"✅ Successfully updated attribute {attribute_id}")
        return updated_attribute
    
    # Additional methods
    
    async def get_by_concept(
        self,
        concept_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attribute]:
        """Get all attributes for a concept"""
        return await self.service.get_by_concept(concept_id, skip, limit)
    
    async def get_required_attributes(self, concept_id: str) -> List[Attribute]:
        """Get all required attributes for a concept"""
        return await self.service.get_required_attributes(concept_id)


# ============================================================================
# ROUTES
# ============================================================================

def get_controller(db = Depends(get_db)) -> AttributeController:
    """Factory function to create AttributeController instance"""
    from src.services.MDE.attribute_service import AttributeService
    from src.repositories.MDE.attribute_repository import AttributeRepository
    from src.repositories.MDE.concept_repository import ConceptRepository
    from src.repositories.MDE.metamodel_repository import MetamodelRepository
    
    attribute_repo = AttributeRepository(db)
    concept_repo = ConceptRepository(db)
    metamodel_repo = MetamodelRepository(db)
    service = AttributeService(attribute_repo, concept_repo, metamodel_repo)
    return AttributeController(service)


@router.get("/concept/{concept_id}", response_model=List[Attribute])
async def get_attributes_by_concept(
    concept_id: str,
    skip: int = 0,
    limit: int = 100,
    controller: AttributeController = Depends(get_controller)
):
    """Get all attributes for a specific concept"""
    return await controller.get_by_concept(concept_id, skip, limit)


@router.get("/metamodel/{metamodel_id}", response_model=List[Attribute])
async def get_attributes_by_metamodel(
    metamodel_id: str,
    skip: int = 0,
    limit: int = 100,
    controller: AttributeController = Depends(get_controller)
):
    """Get all attributes for a specific metamodel"""
    attributes = await controller.service.attribute_repo.get_by_metamodel(metamodel_id, skip, limit)
    return attributes


@router.get("/{attribute_id}", response_model=Attribute)
async def get_attribute(
    attribute_id: str,
    controller: AttributeController = Depends(get_controller)
):
    """Get attribute by ID"""
    attribute = await controller.service.get_by_id(attribute_id)
    if not attribute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found"
        )
    return attribute


@router.post("/", response_model=Attribute, status_code=status.HTTP_201_CREATED)
async def create_attribute(
    attribute_data: AttributeCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: AttributeController = Depends(get_controller)
):
    """Create a new attribute"""
    logger.info(f"Creating attribute: {attribute_data.name} for concept {attribute_data.concept_id}")
    return await controller.create(attribute_data, current_user, db)


@router.put("/{attribute_id}", response_model=Attribute)
async def update_attribute(
    attribute_id: str,
    updates: AttributeUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: AttributeController = Depends(get_controller)
):
    """Update an attribute"""
    return await controller.update(attribute_id, updates, current_user, db)


@router.delete("/{attribute_id}")
async def delete_attribute(
    attribute_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: AttributeController = Depends(get_controller)
):
    """Delete an attribute"""
    await controller.validate_delete(attribute_id, current_user, db)
    success = await controller.service.delete(attribute_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attribute not found"
        )
    
    return {"message": "Attribute deleted successfully"}
