"""
Metamodel Controller - Manage MDE (Model-Driven Engineering) metamodels
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import logging
import uuid

from ..base_controller import BaseController
from ...models.user import User
from ...models import Metamodel, MetamodelCreate, MetamodelUpdate, MetamodelGraphResponse
from ...services.MDE.metamodel_service import MetamodelService
from ...repositories.MDE.metamodel_repository import MetamodelRepository
from ...utils.auth import get_current_user
from ...database import get_db

router = APIRouter(prefix="/api/metamodels", tags=["metamodels"])
logger = logging.getLogger(__name__)


class MetamodelController(BaseController[Metamodel, MetamodelCreate, MetamodelUpdate]):
    """Metamodel Controller with CRUD operations"""
    
    def __init__(self, service: MetamodelService):
        super().__init__(service.repository)
        self.service = service
    
    def get_resource_name(self) -> str:
        return "metamodel"
    
    def get_resource_name_plural(self) -> str:
        return "metamodels"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        """Generate UUID for new metamodel"""
        return str(uuid.uuid4())
    
    async def validate_create(self, data: MetamodelCreate, current_user: User, db) -> Dict[str, Any]:
        """
        Validate metamodel creation
        - Check for name uniqueness
        - Add author information
        """
        logger.info(f"🚀 Creating metamodel: {data.name}")
        
        # Check if metamodel with same name already exists
        existing = await self.service.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Metamodel with name '{data.name}' already exists"
            )
        
        # Prepare data with owner info
        result = data.model_dump()
        result["owner_id"] = current_user.username
        
        # Debug: log the data being sent to repository
        logger.info(f"🔍 Data to create: {result}")
        
        return result
    
    async def validate_update(self, resource_id: str, updates: MetamodelUpdate, current_user: User, db) -> Optional[Dict[str, Any]]:
        """
        Validate metamodel update
        - Check authorization (only author can update)
        - Check name uniqueness if name is being changed
        """
        logger.info(f"🔄 Updating metamodel: {resource_id}")
        
        # Check if metamodel exists
        existing = await self.service.get_by_id(resource_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metamodel {resource_id} not found"
            )
        
        # Check authorization (only author can update)
        if existing.author != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this metamodel"
            )
        
        # Prepare update data
        update_data = updates.model_dump(exclude_unset=True)
        
        # If name is being changed, check for conflicts
        if "name" in update_data and update_data["name"] != existing.name:
            name_conflict = await self.service.get_by_name(update_data["name"])
            if name_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Metamodel with name '{update_data['name']}' already exists"
                )
        
        return update_data
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Dict[str, Any]:
        """
        Validate metamodel deletion
        - Check if exists
        - Check authorization (only author can delete)
        """
        logger.info(f"🗑️  Deleting metamodel: {resource_id}")
        
        # Check if metamodel exists
        existing = await self.service.get_by_id(resource_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metamodel {resource_id} not found"
            )
        
        # Check authorization (only author can delete)
        if existing.author != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this metamodel"
            )
        
        return {"entity_id": resource_id}
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Metamodel]:
        """Metamodels are not synced from GitHub"""
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Metamodels cannot be synced from GitHub"
        )
    
    # Custom methods specific to metamodels
    
    async def validate_metamodel(self, metamodel_id: str) -> Metamodel:
        """Validate a metamodel (change status to 'validated')"""
        logger.info(f"✅ Validating metamodel: {metamodel_id}")
        
        metamodel = await self.service.validate_metamodel(metamodel_id)
        if not metamodel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metamodel {metamodel_id} not found"
            )
        
        return metamodel
    
    async def deprecate_metamodel(self, metamodel_id: str) -> Metamodel:
        """Deprecate a metamodel (change status to 'deprecated')"""
        logger.warning(f"⚠️  Deprecating metamodel: {metamodel_id}")
        
        metamodel = await self.service.deprecate_metamodel(metamodel_id)
        if not metamodel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Metamodel {metamodel_id} not found"
            )
        
        return metamodel
    
    async def get_by_status(self, status: str) -> List[Metamodel]:
        """Get metamodels by status"""
        return await self.service.get_by_status(status)
    
    async def get_by_author(self, author: str) -> List[Metamodel]:
        """Get metamodels by author"""
        return await self.service.get_by_author(author)


# Dependency to get controller instance
def get_metamodel_controller(db = Depends(get_db)) -> MetamodelController:
    """FastAPI dependency to get MetamodelController instance"""
    repository = MetamodelRepository(db)
    service = MetamodelService(repository)
    return MetamodelController(service)


# Route handlers

@router.get("/", response_model=List[Metamodel])
async def list_metamodels(
    status: Optional[str] = None,
    author: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MetamodelController = Depends(get_metamodel_controller)
):
    """
    Get all metamodels with optional filters
    
    - **status**: Filter by status (draft, validated, deprecated)
    - **author**: Filter by author username
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    if status:
        return await controller.get_by_status(status)
    elif author:
        return await controller.get_by_author(author)
    else:
        return await controller.get_all(current_user, db, skip, limit)


@router.get("/{metamodel_id}", response_model=Metamodel)
async def get_metamodel(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MetamodelController = Depends(get_metamodel_controller)
):
    """Get metamodel by ID"""
    return await controller.get_by_id(metamodel_id, current_user, db)


@router.post("/", response_model=Metamodel, status_code=status.HTTP_201_CREATED)
async def create_metamodel(
    metamodel_data: MetamodelCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MetamodelController = Depends(get_metamodel_controller)
):
    """Create a new metamodel"""
    return await controller.create(metamodel_data, current_user, db)


@router.put("/{metamodel_id}", response_model=Metamodel)
async def update_metamodel(
    metamodel_id: str,
    updates: MetamodelUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MetamodelController = Depends(get_metamodel_controller)
):
    """Update a metamodel"""
    return await controller.update(metamodel_id, updates, current_user, db)


@router.delete("/{metamodel_id}")
async def delete_metamodel(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    controller: MetamodelController = Depends(get_metamodel_controller)
):
    """Delete a metamodel"""
    return await controller.delete(metamodel_id, current_user, db)


@router.post("/{metamodel_id}/validate", response_model=Metamodel)
async def validate_metamodel(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    controller: MetamodelController = Depends(get_metamodel_controller)
):
    """Validate a metamodel (change status to 'validated')"""
    return await controller.validate_metamodel(metamodel_id)


@router.post("/{metamodel_id}/deprecate", response_model=Metamodel)
async def deprecate_metamodel(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    controller: MetamodelController = Depends(get_metamodel_controller)
):
    """Deprecate a metamodel (change status to 'deprecated')"""
    return await controller.deprecate_metamodel(metamodel_id)


@router.get("/{metamodel_id}/graph", response_model=MetamodelGraphResponse)
async def get_metamodel_graph(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get complete metamodel graph with all nodes and edges
    
    Returns:
    - metamodel: Complete Metamodel object with all fields
    - nodes: List of all nodes (Concepts, Attributes, Relations)
    - edges: List of all edges (DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF)
    """
    logger.info(f"📊 Getting complete graph for metamodel: {metamodel_id}")
    
    # Créer le service avec tous les repositories
    from ...repositories.MDE.concept_repository import ConceptRepository
    from ...repositories.MDE.attribute_repository import AttributeRepository
    from ...repositories.MDE.relationship_repository import RelationshipRepository
    from ...repositories.MDE.metamodel_edge_repository import MetamodelEdgeRepository
    
    metamodel_repo = MetamodelRepository(db)
    concept_repo = ConceptRepository(db)
    attribute_repo = AttributeRepository(db)
    relationship_repo = RelationshipRepository(db)
    edge_repo = MetamodelEdgeRepository(db)
    
    service = MetamodelService(
        repository=metamodel_repo,
        concept_repository=concept_repo,
        attribute_repository=attribute_repo,
        relationship_repository=relationship_repo,
        edge_repository=edge_repo
    )
    
    try:
        graph_data = await service.get_metamodel_with_graph(metamodel_id)
        logger.info(f"✅ Graph retrieved: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges")
        return graph_data
    except ValueError as e:
        logger.error(f"❌ Error getting graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error getting graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metamodel graph: {str(e)}"
        )
