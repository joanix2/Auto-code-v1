"""
M3 Controller - API endpoints for meta-metamodel configuration

This exposes the M3 type system (NodeType, EdgeType) to the frontend.
"""
from fastapi import APIRouter
from typing import List, Dict, Any
from backend.src.config.m3_config import M3Config
from backend.src.models.graph.node_type import NodeType
from backend.src.models.graph.edge_type import EdgeType


router = APIRouter(prefix="/api/m3", tags=["M3"])


@router.get("/node-types", response_model=List[NodeType])
async def get_node_types() -> List[NodeType]:
    """
    Get all available node types from M3 configuration
    
    Returns:
        List of NodeType objects with id, label, gender, article, etc.
    """
    return M3Config.get_node_types()


@router.get("/node-types/{type_id}", response_model=NodeType)
async def get_node_type(type_id: str) -> NodeType:
    """
    Get a specific node type by ID
    
    Args:
        type_id: The node type ID (e.g., "concept", "attribute", "relation")
        
    Returns:
        NodeType object
    """
    node_type = M3Config.get_node_type(type_id)
    if not node_type:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Node type '{type_id}' not found")
    return node_type


@router.get("/edge-types", response_model=List[EdgeType])
async def get_edge_types() -> List[EdgeType]:
    """
    Get all available edge types from M3 configuration
    
    Returns:
        List of EdgeType objects with constraints
    """
    return M3Config.get_edge_types()


@router.get("/edge-types/{type_id}", response_model=EdgeType)
async def get_edge_type(type_id: str) -> EdgeType:
    """
    Get a specific edge type by ID
    
    Args:
        type_id: The edge type ID (e.g., "domain", "range")
        
    Returns:
        EdgeType object
    """
    edge_type = M3Config.get_edge_type(type_id)
    if not edge_type:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Edge type '{type_id}' not found")
    return edge_type


@router.get("/edge-constraints")
async def get_edge_constraints() -> List[Dict[str, Any]]:
    """
    Get edge constraints for the graph editor
    
    This returns constraints in the format expected by the frontend graph editor,
    with all valid combinations of source/target node types for each edge type.
    
    Returns:
        List of constraint objects:
        {
            "edgeType": "DOMAIN",
            "label": "DOMAIN",
            "sourceNodeType": "relation",
            "targetNodeType": "concept",
            "directed": true
        }
    """
    return M3Config.get_edge_constraints()


@router.get("/config")
async def get_m3_config() -> Dict[str, Any]:
    """
    Get complete M3 configuration (all node types and edge types)
    
    This is a convenience endpoint that returns everything in one call.
    
    Returns:
        {
            "nodeTypes": [...],
            "edgeTypes": [...],
            "edgeConstraints": [...]
        }
    """
    return {
        "nodeTypes": M3Config.get_node_types(),
        "edgeTypes": M3Config.get_edge_types(),
        "edgeConstraints": M3Config.get_edge_constraints()
    }
