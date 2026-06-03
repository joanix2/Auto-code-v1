"""
Edge Controller - API endpoints for metamodel edges
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.database import get_db
from src.models.MDE.M2 import MetamodelEdgeCreate, MetamodelEdgeType, MetamodelEdgeUpdate
from src.models.oauth.user import User
from src.repositories.MDE.M2.metamodel_edge_repository import MetamodelEdgeRepository
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

# Router definition
router = APIRouter(prefix="/api/edges", tags=["edges"])


def get_edge_repository(db=Depends(get_db)):
    """Dependency to get edge repository"""
    return MetamodelEdgeRepository(db)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_edge(
    edge_data: MetamodelEdgeCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    edge_repo: MetamodelEdgeRepository = Depends(get_edge_repository),
) -> dict[str, Any]:
    """
    Create a new edge between two nodes

    Args:
        edge_data: Edge creation data (graph_id, source_id, target_id, edge_type)

    Returns:
        Created edge
    """
    try:
        # Convertir le string en enum si nécessaire (accepter majuscules et minuscules)
        if isinstance(edge_data.edge_type, str):
            edge_type_enum = MetamodelEdgeType(edge_data.edge_type.lower())
        else:
            edge_type_enum = edge_data.edge_type
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge type: {edge_data.edge_type}. Must be one of: {[e.value for e in MetamodelEdgeType]}",
        )

    logger.info(
        f"Creating edge: {edge_type_enum.value} from {edge_data.source_id} to {edge_data.target_id} "
        f"in metamodel {edge_data.graph_id}"
    )

    try:
        edge = await edge_repo.create_edge(
            edge_data.graph_id, edge_data.source_id, edge_data.target_id, edge_type_enum
        )

        logger.info(f"✅ Edge created successfully: {edge.id}")
        # Retourner le dictionnaire formaté pour le frontend avec le champ 'label'
        return edge.to_graph_dict()

    except ValueError as e:
        logger.error(f"❌ Error creating edge: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Unexpected error creating edge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create edge: {str(e)}",
        )


@router.patch("/{edge_id}")
async def update_edge(
    edge_id: str,
    updates: MetamodelEdgeUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    edge_repo: MetamodelEdgeRepository = Depends(get_edge_repository),
):
    """
    Update an edge's metadata (e.g. description)

    Args:
        edge_id: Edge ID (format: {type}-{source_id}-{target_id})
        updates: Fields to update

    Returns:
        Updated edge
    """
    logger.info(f"Patching edge: {edge_id}")

    # Parse the compound edge ID: {edge_type}-{source_id}-{target_id}
    parts = edge_id.split("-", 2)
    if len(parts) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge ID format: {edge_id}. Expected: {{type}}-{{source_id}}-{{target_id}}",
        )

    edge_type_str, source_id, target_id = parts

    try:
        edge_type_enum = MetamodelEdgeType(edge_type_str.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge type: {edge_type_str}. Must be one of: {[e.value for e in MetamodelEdgeType]}",
        )

    update_dict = updates.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    edge = await edge_repo.update_edge(
        source_id, target_id, edge_type_enum, update_dict
    )

    if not edge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge not found: {edge_id}",
        )

    return edge.to_graph_dict()


@router.delete("/{edge_id}")
async def delete_edge_by_id(
    edge_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    edge_repo: MetamodelEdgeRepository = Depends(get_edge_repository),
):
    """
    Delete an edge by its compound ID

    Args:
        edge_id: Edge ID (format: {type}-{source_id}-{target_id})

    Returns:
        Success message
    """
    logger.info(f"Deleting edge by ID: {edge_id}")

    # Parse the compound edge ID
    parts = edge_id.split("-", 2)
    if len(parts) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge ID format: {edge_id}. Expected: {{type}}-{{source_id}}-{{target_id}}",
        )

    edge_type_str, source_id, target_id = parts

    try:
        edge_type_enum = MetamodelEdgeType(edge_type_str.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge type: {edge_type_str}. Must be one of: {[e.value for e in MetamodelEdgeType]}",
        )

    deleted = await edge_repo.delete_edge(source_id, target_id, edge_type_enum)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge not found: {edge_id}",
        )

    return {
        "message": "Edge deleted successfully",
        "edge_id": edge_id,
    }


@router.delete("/{source_id}/{target_id}/{edge_type}")
async def delete_edge(
    source_id: str,
    target_id: str,
    edge_type: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    edge_repo: MetamodelEdgeRepository = Depends(get_edge_repository),
):
    """
    Delete an edge between two nodes

    Args:
        source_id: ID du noeud source
        target_id: ID du noeud cible
        edge_type: Type d'edge (domain, range, has_attribute, subclass_of)

    Returns:
        Success message
    """
    try:
        # Convertir le string en enum (accepter majuscules et minuscules)
        edge_type_enum = MetamodelEdgeType(edge_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge type: {edge_type}. Must be one of: {[e.value for e in MetamodelEdgeType]}",
        )

    logger.info(f"Deleting edge: {edge_type} from {source_id} to {target_id}")

    deleted = await edge_repo.delete_edge(source_id, target_id, edge_type_enum)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge not found: {edge_type} from {source_id} to {target_id}",
        )

    return {
        "message": "Edge deleted successfully",
        "source_id": source_id,
        "target_id": target_id,
        "edge_type": edge_type,
    }
