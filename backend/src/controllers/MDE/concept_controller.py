"""
Concept Controller - API endpoints for concepts
"""
from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
import logging
from uuid import uuid4

from ..base_controller import BaseController
from src.services.MDE.concept_service import ConceptService
from src.models.MDE.concept import Concept, ConceptCreate, ConceptUpdate
from src.models.user import User

logger = logging.getLogger(__name__)


class ConceptController(BaseController[Concept, ConceptCreate, ConceptUpdate]):
    """Controller for concept CRUD operations"""
    
    def __init__(self, service: ConceptService):
        self.service = service
    
    def get_resource_name(self) -> str:
        return "concept"
    
    def get_resource_name_plural(self) -> str:
        return "concepts"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        """Generate unique ID for concept"""
        return str(uuid4())
    
    async def validate_create(self, data: ConceptCreate, current_user: User, db) -> Dict[str, Any]:
        """Validate concept creation"""
        validated_data = data.model_dump()
        
        # Metamodel existence is validated in service
        
        return validated_data
    
    async def validate_update(
        self,
        resource_id: str,
        updates: ConceptUpdate,
        current_user: User,
        db
    ) -> Optional[Dict[str, Any]]:
        """Validate concept update"""
        # Check if concept exists
        concept = await self.service.get_by_id(resource_id)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept not found"
            )
        
        return None  # No modifications needed
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Concept:
        """Validate concept deletion"""
        # Check if concept exists
        concept = await self.service.get_by_id(resource_id)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept not found"
            )
        
        return concept
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Concept]:
        """Sync concepts from GitHub (not implemented)"""
        return []
    
    # Override create to use service
    async def create(self, data: ConceptCreate, current_user: User, db) -> Concept:
        """Create a new concept"""
        try:
            validated_data = await self.validate_create(data, current_user, db)
            concept = await self.service.create(validated_data)
            logger.info(f"Created concept {concept.id}")
            return concept
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Concept creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create concept: {str(e)}"
            )
    
    # Additional methods
    
    async def get_by_metamodel(
        self,
        metamodel_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Concept]:
        """Get all concepts for a metamodel"""
        return await self.service.get_by_metamodel(metamodel_id, skip, limit)
    
    async def get_with_attributes(self, concept_id: str) -> Dict[str, Any]:
        """Get concept with all its attributes"""
        result = await self.service.get_with_attributes(concept_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept not found"
            )
        return result
    
    async def update_position(
        self,
        concept_id: str,
        x: float,
        y: float,
        current_user: User,
        db
    ) -> Concept:
        """Update concept position in graph"""
        concept = await self.service.update_position(concept_id, x, y)
        if not concept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Concept not found"
            )
        return concept
