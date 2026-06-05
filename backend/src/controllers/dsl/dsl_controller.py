"""
DSLGraph Controller - Manage MDE (Model-Driven Engineering) dsls
"""

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ...database import get_db
from ...models import DSLGraph, DSLGraphCreate, DSLGraphResponse, DSLGraphUpdate
from ...models.dsl import DSLGraphFullResponse
from ...models.oauth.user import User
from ...repositories.dsl.dsl_repository import DSLRepository
from ...services.dsl.dsl_service import DSLService
from ...utils.auth import get_current_user
from ..base_controller import BaseController

router = APIRouter(prefix="/api/dsls", tags=["dsls"])
logger = logging.getLogger(__name__)


class DSLController(BaseController[DSLGraph, DSLGraphCreate, DSLGraphUpdate]):
    """DSLGraph Controller with CRUD operations"""

    def __init__(self, service: DSLService):
        super().__init__(service.repository)
        self.service = service

    def get_resource_name(self) -> str:
        return "dsl"

    def get_resource_name_plural(self) -> str:
        return "dsls"

    async def generate_id(self, data: dict[str, Any]) -> str:
        """Generate UUID for new dsl"""
        return str(uuid.uuid4())

    async def validate_create(
        self, data: DSLGraphCreate, current_user: User, db
    ) -> dict[str, Any]:
        """
        Validate dsl creation
        - Check for name uniqueness
        - Add author information
        """
        logger.info(f"🚀 Creating dsl: {data.name}")

        # Check if dsl with same name already exists
        existing = await self.service.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"DSLGraph with name '{data.name}' already exists",
            )

        # Prepare data with owner info - only keep fields that DSLGraph accepts
        result = data.model_dump()
        result["owner_id"] = current_user.username

        # Filter to only DSLGraph fields (exclude DSLGraphCreate-only fields)
        dsl_fields = set(DSLGraph.model_fields.keys())
        filtered = {k: v for k, v in result.items() if k in dsl_fields or k == "owner_id"}
        # Generate ID if not present
        if "id" not in filtered:
            filtered["id"] = str(uuid.uuid4())
        # Ensure description is string, not None
        if "description" in filtered and filtered["description"] is None:
            filtered["description"] = ""

        logger.info(f"🔍 Data to create: {filtered}")
        return filtered

    async def validate_update(
        self, resource_id: str, updates: DSLGraphUpdate, current_user: User, db
    ) -> dict[str, Any] | None:
        """
        Validate dsl update
        - Check authorization (only author can update)
        - Check name uniqueness if name is being changed
        """
        logger.info(f"🔄 Updating dsl: {resource_id}")

        # Check if dsl exists
        existing = await self.service.get_by_id(resource_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DSLGraph {resource_id} not found"
            )

        # Check authorization (only author can update)
        if existing.author != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this dsl",
            )

        # Prepare update data
        update_data = updates.model_dump(exclude_unset=True)

        # If name is being changed, check for conflicts
        if "name" in update_data and update_data["name"] != existing.name:
            name_conflict = await self.service.get_by_name(update_data["name"])
            if name_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"DSLGraph with name '{update_data['name']}' already exists",
                )

        return update_data

    async def validate_delete(self, resource_id: str, current_user: User, db) -> dict[str, Any]:
        """
        Validate dsl deletion
        - Check if exists
        - Check authorization (only author can delete)
        """
        logger.info(f"🗑️  Deleting dsl: {resource_id}")

        # Check if dsl exists
        existing = await self.service.get_by_id(resource_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DSLGraph {resource_id} not found"
            )

        # Check authorization (only author can delete)
        if existing.author != current_user.username:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this dsl",
            )

        return {"entity_id": resource_id}

    async def sync_from_github(
        self, github_token: str, current_user: User, **kwargs
    ) -> list[DSLGraph]:
        """DSLGraphs are not synced from GitHub"""
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="DSLGraphs cannot be synced from GitHub",
        )

    # Custom methods specific to dsls

    async def validate_dsl(self, dsl_id: str) -> DSLGraph:
        """Validate a dsl (change status to 'validated')"""
        logger.info(f"✅ Validating dsl: {dsl_id}")

        dsl = await self.service.validate_dsl(dsl_id)
        if not dsl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DSLGraph {dsl_id} not found"
            )

        return dsl

    async def deprecate_dsl(self, dsl_id: str) -> DSLGraph:
        """Deprecate a dsl (change status to 'deprecated')"""
        logger.warning(f"⚠️  Deprecating dsl: {dsl_id}")

        dsl = await self.service.deprecate_dsl(dsl_id)
        if not dsl:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DSLGraph {dsl_id} not found"
            )

        return dsl

    async def get_by_status(self, status: str) -> list[DSLGraph]:
        """Get dsls by status"""
        return await self.service.get_by_status(status)

    async def get_by_author(self, author: str) -> list[DSLGraph]:
        """Get dsls by author"""
        return await self.service.get_by_author(author)


# Dependency to get controller instance
def get_dsl_controller(db=Depends(get_db)) -> DSLController:
    """FastAPI dependency to get DSLController instance"""
    repository = DSLRepository(db)
    service = DSLService(repository)
    return DSLController(service)


# Route handlers


@router.get("/", response_model=list[DSLGraph])
async def list_dsls(
    status: str | None = None,
    author: str | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLController = Depends(get_dsl_controller),
):
    """
    Get all dsls with optional filters

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


@router.get("/{dsl_id}", response_model=DSLGraph)
async def get_dsl(
    dsl_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLController = Depends(get_dsl_controller),
):
    """Get dsl by ID"""
    return await controller.get_by_id(dsl_id, current_user, db)


@router.post("/", response_model=DSLGraph, status_code=status.HTTP_201_CREATED)
async def create_dsl(
    dsl_data: DSLGraphCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLController = Depends(get_dsl_controller),
):
    """Create a new dsl"""
    return await controller.create(dsl_data, current_user, db)


@router.put("/{dsl_id}", response_model=DSLGraph)
async def update_dsl(
    dsl_id: str,
    updates: DSLGraphUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLController = Depends(get_dsl_controller),
):
    """Update a dsl"""
    return await controller.update(dsl_id, updates, current_user, db)


@router.delete("/{dsl_id}")
async def delete_dsl(
    dsl_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: DSLController = Depends(get_dsl_controller),
):
    """Delete a dsl"""
    return await controller.delete(dsl_id, current_user, db)


@router.post("/{dsl_id}/validate", response_model=DSLGraph)
async def validate_dsl(
    dsl_id: str,
    current_user: User = Depends(get_current_user),
    controller: DSLController = Depends(get_dsl_controller),
):
    """Validate a dsl (change status to 'validated')"""
    return await controller.validate_dsl(dsl_id)


@router.post("/{dsl_id}/deprecate", response_model=DSLGraph)
async def deprecate_dsl(
    dsl_id: str,
    current_user: User = Depends(get_current_user),
    controller: DSLController = Depends(get_dsl_controller),
):
    """Deprecate a dsl (change status to 'deprecated')"""
    return await controller.deprecate_dsl(dsl_id)


@router.get("/{dsl_id}/graph", response_model=DSLGraphFullResponse)
async def get_dsl_graph(
    dsl_id: str, current_user: User = Depends(get_current_user), db=Depends(get_db)
):
    """
    Get complete dsl graph with all nodes and edges

    Returns:
    - dsl: Complete DSLGraph object with all fields
    - nodes: List of all nodes (DSLConcepts, DSLAttributes, Relations)
    - edges: List of all edges (DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF)
    """
    logger.info(f"📊 Getting complete graph for dsl: {dsl_id}")

    # Créer le service avec tous les repositories
    from ...repositories.dsl.dsl_attribute_repository import DSLAttributeRepository
    from ...repositories.dsl.dsl_concept_repository import DSLConceptRepository
    from ...repositories.dsl.dsl_edge_repository import DSLEdgeRepository
    from ...repositories.dsl.dsl_relation_repository import DSLRelationRepository

    dsl_repo = DSLRepository(db)
    concept_repo = DSLConceptRepository(db)
    attribute_repo = DSLAttributeRepository(db)
    relationship_repo = DSLRelationRepository(db)
    edge_repo = DSLEdgeRepository(db)

    service = DSLService(
        repository=dsl_repo,
        dsl_concept_repository=concept_repo,
        dsl_attribute_repository=attribute_repo,
        relationship_repository=relationship_repo,
        dsl_edge_repository=edge_repo,
    )

    try:
        graph_data = await service.get_dsl_with_graph(dsl_id)

        # Edge constraints are included in the dsl object via allowed_edge_types
        # The DSLGraphResponse already includes edgeConstraints field
        # which will be automatically populated from the dsl's allowed_edge_types

        logger.info(
            f"✅ Graph retrieved: {len(graph_data['nodes'])} nodes, {len(graph_data['edges'])} edges"
        )
        return graph_data
    except ValueError as e:
        logger.error(f"❌ Error getting graph: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Unexpected error getting graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dsl graph: {str(e)}",
        )
