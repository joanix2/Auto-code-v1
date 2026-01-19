"""
Edge Controller - API endpoints for metamodel edges
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
import logging

from src.models.MDE.M2 import MetamodelEdge, MetamodelEdgeType, MetamodelEdgeCreate
from src.models.user import User
from src.database import get_db
from src.utils.auth import get_current_user
from src.repositories.MDE.metamodel_edge_repository import MetamodelEdgeRepository

logger = logging.getLogger(__name__)

# Router definition
router = APIRouter(prefix="/api/edges", tags=["edges"])


def get_edge_repository(db = Depends(get_db)):
    """Dependency to get edge repository"""
    return MetamodelEdgeRepository(db)


@router.post("/", response_model=MetamodelEdge, status_code=status.HTTP_201_CREATED)
async def create_edge(
    edge_data: MetamodelEdgeCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    edge_repo: MetamodelEdgeRepository = Depends(get_edge_repository)
):
    """
    Create a new edge between two nodes
    
    Args:
        edge_data: Edge creation data (graph_id, source_id, target_id, edge_type)
    
    Returns:
        Created edge
    """
    try:
        # Convertir le string en enum si nécessaire
        if isinstance(edge_data.edge_type, str):
            edge_type_enum = MetamodelEdgeType(edge_data.edge_type)
        else:
            edge_type_enum = edge_data.edge_type
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge type: {edge_data.edge_type}. Must be one of: {[e.value for e in MetamodelEdgeType]}"
        )
    
    logger.info(
        f"Creating edge: {edge_type_enum.value} from {edge_data.source_id} to {edge_data.target_id} "
        f"in metamodel {edge_data.graph_id}"
    )
    
    try:
        edge = await edge_repo.create_edge(
            edge_data.graph_id,
            edge_data.source_id,
            edge_data.target_id,
            edge_type_enum
        )
        
        logger.info(f"✅ Edge created successfully: {edge.id}")
        return edge
        
    except ValueError as e:
        logger.error(f"❌ Error creating edge: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"❌ Unexpected error creating edge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create edge: {str(e)}"
        )


@router.delete("/{source_id}/{target_id}/{edge_type}")
async def delete_edge(
    source_id: str,
    target_id: str,
    edge_type: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
    edge_repo: MetamodelEdgeRepository = Depends(get_edge_repository)
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
        # Convertir le string en enum
        edge_type_enum = MetamodelEdgeType(edge_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid edge type: {edge_type}. Must be one of: {[e.value for e in MetamodelEdgeType]}"
        )
    
    logger.info(f"Deleting edge: {edge_type} from {source_id} to {target_id}")
    
    deleted = await edge_repo.delete_edge(source_id, target_id, edge_type_enum)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edge not found: {edge_type} from {source_id} to {target_id}"
        )
    
    return {
        "message": "Edge deleted successfully",
        "source_id": source_id,
        "target_id": target_id,
        "edge_type": edge_type
    }
