"""
Attribute Controller - API endpoints for attributes
"""
from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
import logging
from uuid import uuid4

from ..base_controller import BaseController
from src.services.MDE.attribute_service import AttributeService
from src.models.MDE.attribute import Attribute, AttributeCreate, AttributeUpdate
from src.models.user import User

logger = logging.getLogger(__name__)


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
