"""
Query Controller - REST API endpoints for graph query operations

Provides endpoints for selectors, entity tree extraction, and
graph traversal. All endpoints are read-only (GET operations).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.database import get_db
from src.models.oauth.user import User
from src.services.query.query_service import QueryService
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/query", tags=["query"])


# ------------------------------------------------------------------
# Dependencies
# ------------------------------------------------------------------

def get_query_service(db=Depends(get_db)) -> QueryService:
    """FastAPI dependency to get a QueryService instance."""
    return QueryService(db)


# ------------------------------------------------------------------
# Selector endpoints
# ------------------------------------------------------------------

@router.get("/nodes/{kind}")
async def get_nodes_by_kind(
    kind: str,
    graph_id: str | None = Query(None, description="Scope to a specific graph/metamodel ID"),
    current_user: User = Depends(get_current_user),
    query_service: QueryService = Depends(get_query_service),
):
    """Get all nodes of a given kind.
    
    Args:
        kind: Node type — 'concept', 'attribute', 'relation', or 'metamodel'.
        graph_id: Optional graph/metamodel ID to scope results.
    
    Returns:
        List of node objects.
    """
    logger.info(f"Query: nodes by kind '{kind}' (graph_id={graph_id})")
    try:
        nodes = query_service.get_nodes_by_kind(kind, graph_id)
        return {"kind": kind, "count": len(nodes), "data": nodes}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/edges/{kind}")
async def get_edges_by_kind(
    kind: str,
    graph_id: str | None = Query(None, description="Scope to a specific graph/metamodel ID"),
    current_user: User = Depends(get_current_user),
    query_service: QueryService = Depends(get_query_service),
):
    """Get all edges of a given kind.
    
    Args:
        kind: Edge type — 'domain', 'range', 'has_attribute', or 'subclass_of'.
        graph_id: Optional graph/metamodel ID to scope results.
    
    Returns:
        List of edge objects.
    """
    logger.info(f"Query: edges by kind '{kind}' (graph_id={graph_id})")
    try:
        edges = query_service.get_edges_by_kind(kind, graph_id)
        return {"kind": kind, "count": len(edges), "data": edges}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/node/{node_id}/neighbors")
async def get_neighbors(
    node_id: str,
    graph_id: str | None = Query(None, description="Scope to a specific graph/metamodel ID"),
    current_user: User = Depends(get_current_user),
    query_service: QueryService = Depends(get_query_service),
):
    """Get all neighboring nodes connected to a given node via any edge.
    
    Args:
        node_id: ID of the node.
        graph_id: Optional graph/metamodel ID to scope results.
    
    Returns:
        List of neighbor node objects with '_via' metadata.
    """
    logger.info(f"Query: neighbors of node '{node_id}' (graph_id={graph_id})")
    neighbors = query_service.get_neighbors(node_id, graph_id)
    return {"node_id": node_id, "count": len(neighbors), "data": neighbors}


@router.get("/node/{node_id}/edges")
async def get_incident_edges(
    node_id: str,
    graph_id: str | None = Query(None, description="Scope to a specific graph/metamodel ID"),
    current_user: User = Depends(get_current_user),
    query_service: QueryService = Depends(get_query_service),
):
    """Get all edges incident to a given node.
    
    Args:
        node_id: ID of the node.
        graph_id: Optional graph/metamodel ID to scope results.
    
    Returns:
        List of edge objects with direction metadata.
    """
    logger.info(f"Query: incident edges of node '{node_id}' (graph_id={graph_id})")
    edges = query_service.get_incident_edges(node_id, graph_id)
    return {"node_id": node_id, "count": len(edges), "data": edges}


@router.get("/tree/{root_id}")
async def get_entity_tree(
    root_id: str,
    max_depth: int = Query(
        5, ge=1, le=20, description="Maximum recursion depth (1-20)"
    ),
    graph_id: str | None = Query(None, description="Scope to a specific graph/metamodel ID"),
    current_user: User = Depends(get_current_user),
    query_service: QueryService = Depends(get_query_service),
):
    """Get a recursive JSON entity tree rooted at a given node.
    
    The tree structure is:
    ```json
    {
      "entity": { node attributes },
      "fields": [ attribute-like connected nodes ],
      "relations": [ recursive entity trees ]
    }
    ```
    
    This structure is designed for direct consumption by Jinja2 templates.
    Cycle detection prevents infinite recursion.
    
    Args:
        root_id: ID of the root node.
        max_depth: Maximum recursion depth (default 5, max 20).
        graph_id: Optional graph/metamodel ID to scope results.
    
    Returns:
        Entity tree dict, or 404 if the root node is not found.
    """
    logger.info(
        f"Query: entity tree for '{root_id}' (max_depth={max_depth}, graph_id={graph_id})"
    )
    tree = query_service.get_entity_tree(
        root_id=root_id, max_depth=max_depth, graph_id=graph_id
    )
    if tree is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{root_id}' not found",
        )
    return tree


@router.post("/pattern")
async def find_pattern(
    pattern: list[dict[str, Any]],
    graph_id: str | None = Query(None, description="Scope to a specific graph/metamodel ID"),
    current_user: User = Depends(get_current_user),
    query_service: QueryService = Depends(get_query_service),
):
    """Find sub-graphs matching a structural pattern.
    
    Each pattern element is a dict with:
    - 'alias': str (variable name for the match)
    - 'kind': str | None (node kind)
    - 'edges': list of edge constraints
    
    Example:
    ```json
    [
      {"alias": "a", "kind": "concept"},
      {"alias": "b", "kind": "concept",
       "edges": [{"to": "a", "type": "SUBCLASS_OF"}]}
    ]
    ```
    
    Returns:
        List of matched sub-graphs.
    """
    logger.info(f"Query: pattern matching (graph_id={graph_id})")
    matches = query_service.find_pattern(pattern, graph_id)
    return {"count": len(matches), "data": matches}
