"""
Concept Routes - API endpoints for MDE concepts
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
import logging

from .concept_controller import ConceptController
from src.models.MDE.concept import Concept, ConceptCreate, ConceptUpdate
from src.models.user import User
from src.services.MDE.concept_service import ConceptService
from src.repositories.MDE.concept_repository import ConceptRepository
from src.utils.auth import get_current_user
from src.database import get_db

router = APIRouter(prefix="/api/concepts", tags=["concepts"])
logger = logging.getLogger(__name__)


# Dependency to get controller instance
def get_concept_controller(db = Depends(get_db)) -> ConceptController:
    """FastAPI dependency to get ConceptController instance"""
    from src.repositories.MDE.metamodel_repository import MetamodelRepository
    
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
    controller: ConceptController = Depends(get_concept_controller)
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
    controller: ConceptController = Depends(get_concept_controller)
):
    """Get concept by ID"""
    return await controller.get_by_id(concept_id, current_user, db)


@router.get("/{concept_id}/with-attributes")
async def get_concept_with_attributes(
    concept_id: str,
    current_user: User = Depends(get_current_user),
    controller: ConceptController = Depends(get_concept_controller)
):
    """Get concept with all its attributes"""
    return await controller.get_with_attributes(concept_id)


@router.post("/", response_model=Concept, status_code=status.HTTP_201_CREATED)
async def create_concept(
    concept_data: ConceptCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_concept_controller)
):
    """Create a new concept"""
    logger.info(f"Creating concept: {concept_data.name} for graph {concept_data.graph_id}")
    try:
        return await controller.create(concept_data, current_user, db)
    except Exception as e:
        logger.error(f"❌ Error creating concept: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{concept_id}", response_model=Concept)
async def update_concept(
    concept_id: str,
    updates: ConceptUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_concept_controller)
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
    controller: ConceptController = Depends(get_concept_controller)
):
    """Update concept position in graph visualization"""
    return await controller.update_position(concept_id, x, y, current_user, db)


@router.delete("/{concept_id}")
async def delete_concept(
    concept_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: ConceptController = Depends(get_concept_controller)
):
    """Delete a concept"""
    return await controller.delete(concept_id, current_user, db)
