"""
Concept Controller - Business logic layer for MDE concepts
Combined controller and routes in single file
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
import logging

from src.controllers.base_controller import BaseController
from src.models.MDE.metamodel.concept import Concept, ConceptCreate, ConceptUpdate
from src.models.user import User
from src.services.MDE.concept_service import ConceptService
from src.repositories.MDE.concept_repository import ConceptRepository
from src.repositories.MDE.metamodel_repository import MetamodelRepository
from src.utils.auth import get_current_user
from src.database import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/concepts", tags=["concepts"])


class ConceptController(BaseController[Concept, ConceptCreate, ConceptUpdate]):
    """Controller for concept operations following layered architecture"""

    def __init__(self, service: ConceptService):
        super().__init__(service)
        self.service = service

    async def validate_create(self, data: ConceptCreate, current_user: User, db) -> ConceptCreate:
        """Validate concept creation data"""
        if not data.name or len(data.name.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Concept name must be at least 2 characters"
            )
        return data

    async def validate_update(self, id: str, data: ConceptUpdate, current_user: User, db) -> ConceptUpdate:
        """Validate concept update data"""
        if data.name is not None and len(data.name.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Concept name must be at least 2 characters"
            )
        return data

    async def create(self, data: ConceptCreate, current_user: User, db) -> Concept:
        """Create a new concept"""
        validated_data = await self.validate_create(data, current_user, db)
        return await self.service.create(validated_data)

    async def update(self, id: str, data: ConceptUpdate, current_user: User, db) -> Concept:
        """Update an existing concept"""
        validated_data = await self.validate_update(id, data, current_user, db)
        # Convert Pydantic model to dict, excluding unset values
        update_dict = validated_data.model_dump(exclude_unset=True)
        logger.info(f"🔍 Updating concept {id} with data: {update_dict}")
        
        updated_concept = await self.service.update(id, update_dict)
        
        if not updated_concept:
            logger.error(f"❌ service.update returned None for concept {id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concept {id} not found"
            )
        
        logger.info(f"✅ Successfully updated concept {id}")
        return updated_concept

    async def delete(self, id: str, current_user: User, db) -> bool:
        """Delete a concept"""
        return await self.service.delete(id)

    # Additional concept-specific methods
    async def get_by_metamodel(self, metamodel_id: str, skip: int = 0, limit: int = 100) -> List[Concept]:
        """Get concepts by metamodel ID"""
        return await self.service.get_by_metamodel(metamodel_id, skip, limit)

    async def get_with_attributes(self, concept_id: str) -> dict:
        """Get concept with all its attributes"""
        return await self.service.get_with_attributes(concept_id)

    async def update_position(self, concept_id: str, x: float, y: float, current_user: User, db) -> Concept:
        """Update concept position in graph visualization"""
        return await self.service.update_position(concept_id, x, y)

# Dependency to get controller instance
def get_controller(db = Depends(get_db)) -> ConceptController:
    """FastAPI dependency to get ConceptController instance"""
    concept_repository = ConceptRepository(db)
    metamodel_repository = MetamodelRepository(db)
    service = ConceptService(concept_repository, metamodel_repository)
    return ConceptController(service)

@router.get("/", response_model=List[Concept])
async def list_concepts(
    metamodel_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_controller)
):
    """
    Get all concepts with optional filters
    
    - **metamodel_id**: Filter by metamodel ID
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    if metamodel_id:
        return await controller.get_by_metamodel(metamodel_id, skip, limit)
    else:
        return await controller.get_all(current_user, db, skip, limit)

@router.get("/{concept_id}", response_model=Concept)
async def get_concept(
    concept_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_controller)
):
    """Get concept by ID"""
    return await controller.get_by_id(concept_id, current_user, db)

@router.get("/{concept_id}/with-attributes")
async def get_concept_with_attributes(
    concept_id: str,
    current_user: User = Depends(get_current_user),
    controller: ConceptController = Depends(get_controller)
):
    """Get concept with all its attributes"""
    return await controller.get_with_attributes(concept_id)

@router.post("/", response_model=Concept, status_code=status.HTTP_201_CREATED)
async def create_concept(
    concept_data: ConceptCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_controller)
):
    """Create a new concept"""
    logger.info(f"Creating concept: {concept_data.name} for graph {concept_data.graph_id}")
    return await controller.create(concept_data, current_user, db)

@router.put("/{concept_id}", response_model=Concept)
async def update_concept(
    concept_id: str,
    updates: ConceptUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_controller)
):
    """Update a concept"""
    return await controller.update(concept_id, updates, current_user, db)

@router.patch("/{concept_id}/position")
async def update_concept_position(
    concept_id: str,
    x: float,
    y: float,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_controller)
):
    """Update concept position in graph visualization"""
    return await controller.update_position(concept_id, x, y, current_user, db)

@router.delete("/{concept_id}")
async def delete_concept(
    concept_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_controller)
):
    """Delete a concept"""
    logger.info(f"🗑️ DELETE request for concept {concept_id}")
    deleted = await controller.delete(concept_id, current_user, db)
    
    if not deleted:
        logger.error(f"❌ Failed to delete concept {concept_id} - not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept {concept_id} not found"
        )
    
    logger.info(f"✅ Successfully deleted concept {concept_id}")
    return {"message": "Concept deleted successfully", "id": concept_id}
