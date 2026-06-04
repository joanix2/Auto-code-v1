"""Inheritance Controller — REST API endpoints for graph inheritance.

Endpoints:
- ``POST /api/inheritance/set-parent`` — register a parent for a child graph
- ``GET /api/inheritance/{graph_id}/inherited`` — get inherited (merged) graph
- ``GET /api/inheritance/{graph_id}/chain`` — get inheritance chain
- ``GET /api/inheritance/{graph_id}/origin/{element_id}`` — trace element origin
- ``GET /api/inheritance/{graph_id}/parents`` — list parent graphs
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

from src.database import get_db
from src.models.oauth.user import User
from src.services.inheritance import (
    InheritanceConfig,
    InheritanceService,
    InheritanceType,
    InheritedElement,
)
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inheritance", tags=["inheritance"])

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class SetParentRequest(BaseModel):
    """Request body for POST /api/inheritance/set-parent."""

    config: InheritanceConfig
    child_graph: dict[str, Any] | None = None
    parent_graph: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------
# Maps graph_id -> full IR graph dict.  In production this would be backed
# by Neo4j or another persistent store.  The `set-parent` endpoint populates
# this store; the read endpoints query it.
_GRAPH_STORE: dict[str, dict[str, Any]] = {}

# Maps child_id -> InheritanceConfig for quick lookup.
_CONFIG_STORE: dict[str, InheritanceConfig] = {}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/set-parent")
async def set_parent(
    body: SetParentRequest,
    current_user: User = Depends(get_current_user),
):
    """Register an inheritance relationship.

    The request body must include at least ``InheritanceConfig`` fields:

    .. code-block:: json

        {
            "parent_id": "graph-parent-1",
            "child_id": "graph-child-1",
            "inheritance_type": "FULL"
        }

    Optionally include ``child_graph`` and/or ``parent_graph`` as full
    IR JSON dicts if you want the store to hold the graph data for
    subsequent ``/inherited`` / ``/chain`` queries.

    Returns the stored config.
    """
    config = body.config
    logger.info(
        f"set_parent: child={config.child_id}, "
        f"parent={config.parent_id}, type={config.inheritance_type.value}"
    )

    if config.child_id == config.parent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A graph cannot be its own parent",
        )

    # Check for circular inheritance
    if _would_create_circular(config):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Setting parent '{config.parent_id}' for child "
            f"'{config.child_id}' would create a circular inheritance",
        )

    # Store config
    _CONFIG_STORE[config.child_id] = config

    # Store graph data if provided
    if body.child_graph:
        meta = body.child_graph.setdefault("metadata", {})
        meta["id"] = config.child_id
        meta["parent_id"] = config.parent_id
        meta["inheritance_type"] = config.inheritance_type.value
        _GRAPH_STORE[config.child_id] = body.child_graph

    if body.parent_graph:
        body.parent_graph.setdefault("metadata", {})["id"] = config.parent_id
        _GRAPH_STORE[config.parent_id] = body.parent_graph

    return {
        "message": "Parent set successfully",
        "config": config.model_dump(),
    }


@router.get("/{graph_id}/inherited")
async def get_inherited_graph(
    graph_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the fully inherited (merged) graph.

    Resolves inheritance from all ancestors and returns a complete
    IR graph dict with merged nodes, edges, and metadata.
    """
    logger.info(f"get_inherited_graph: {graph_id}")

    child_graph = _resolve_graph(graph_id)
    if child_graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_id}' not found in store",
        )

    parent_id = InheritanceService.get_parent(child_graph)
    if parent_id is None:
        # No parent — return the graph as-is
        return {
            "graph_id": graph_id,
            "inherited": False,
            "graph": child_graph,
        }

    parent_graph = _resolve_graph(parent_id)
    if parent_graph is None:
        # Parent not found in store — cannot resolve inheritance
        logger.warning(
            f"Parent graph '{parent_id}' not found for child '{graph_id}'"
        )
        return {
            "graph_id": graph_id,
            "inherited": False,
            "graph": child_graph,
        }

    # Walk the chain to merge all ancestors
    merged = _resolve_full_chain(child_graph, parent_graph)

    return {
        "graph_id": graph_id,
        "inherited": True,
        "graph": merged,
    }


@router.get("/{graph_id}/chain")
async def get_chain(
    graph_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get the inheritance chain for a graph, from child to root ancestor."""
    logger.info(f"get_chain: {graph_id}")

    child_graph = _resolve_graph(graph_id)
    if child_graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_id}' not found in store",
        )

    all_graphs = _build_full_registry()

    try:
        chain = InheritanceService.get_inheritance_chain(child_graph, all_graphs)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {
        "graph_id": graph_id,
        "chain": [t.model_dump() for t in chain],
        "length": len(chain),
    }


@router.get("/{graph_id}/origin/{element_id}")
async def get_origin(
    graph_id: str,
    element_id: str,
    current_user: User = Depends(get_current_user),
):
    """Trace the origin of a specific node or edge in an inherited graph."""
    logger.info(f"get_origin: element '{element_id}' in graph '{graph_id}'")

    child_graph = _resolve_graph(graph_id)
    if child_graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_id}' not found in store",
        )

    parent_id = InheritanceService.get_parent(child_graph)
    if parent_id is None:
        # No parent — check if element is local
        origin = _check_local_element(element_id, graph_id, child_graph)
        if origin is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Element '{element_id}' not found in graph '{graph_id}'",
            )
        return origin.model_dump()

    parent_graph = _resolve_graph(parent_id)
    if parent_graph is None:
        # Parent not in store, check local only
        origin = _check_local_element(element_id, graph_id, child_graph)
        if origin is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Element '{element_id}' not found in graph '{graph_id}'",
            )
        return origin.model_dump()

    all_graphs = _build_full_registry()
    origin = InheritanceService.get_element_origin(
        element_id=element_id,
        child_graph_data=child_graph,
        parent_graph_data=parent_graph,
        all_graphs=all_graphs,
    )

    if origin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Element '{element_id}' not found in inheritance chain",
        )

    return origin.model_dump()


@router.get("/{graph_id}/parents")
async def list_parents(
    graph_id: str,
    current_user: User = Depends(get_current_user),
):
    """List all parent graphs for the given graph.

    Supports both single-parent (``parent_id``) and multi-parent
    (``parent_ids``) configurations.
    """
    logger.info(f"list_parents: {graph_id}")

    child_graph = _resolve_graph(graph_id)
    if child_graph is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph '{graph_id}' not found in store",
        )

    all_graphs = _build_full_registry()
    parents = InheritanceService.get_multiple_parents(child_graph, all_graphs)

    return {
        "graph_id": graph_id,
        "parent_count": len(parents),
        "parents": [
            {
                "id": _get_graph_id(p),
                "name": p.get("metadata", {}).get("name", ""),
                "description": p.get("metadata", {}).get("description"),
            }
            for p in parents
        ],
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


_META_KEY = "metadata"


def _get_graph_id(graph_data: dict[str, Any]) -> str:
    """Extract the graph ID from an IR JSON graph dict."""
    meta = graph_data.get(_META_KEY, {})
    return str(meta.get("id", ""))


def _resolve_graph(graph_id: str) -> dict[str, Any] | None:
    """Resolve a graph dict by ID, checking in-memory store then config."""
    # 1. Check full graph store
    if graph_id in _GRAPH_STORE:
        return dict(_GRAPH_STORE[graph_id])

    # 2. Check config store — build a minimal graph
    config = _CONFIG_STORE.get(graph_id)
    if config:
        meta: dict[str, Any] = {"id": config.child_id}
        if config.parent_id:
            meta["parent_id"] = config.parent_id
        meta["inheritance_type"] = config.inheritance_type.value
        return {_META_KEY: meta, "nodes": [], "edges": []}

    # 3. Check if it's referenced as a parent in any config
    for child_id, cfg in _CONFIG_STORE.items():
        if cfg.parent_id == graph_id:
            return {_META_KEY: {"id": graph_id}, "nodes": [], "edges": []}

    return None


def _build_full_registry() -> dict[str, dict[str, Any]]:
    """Build a complete ``{graph_id: graph_dict}`` registry from all stores."""
    registry: dict[str, dict[str, Any]] = {}

    # Add all full graph data
    for gid, gdata in _GRAPH_STORE.items():
        registry[gid] = dict(gdata)

    # Add minimal entries from config store
    for child_id, config in _CONFIG_STORE.items():
        if child_id not in registry:
            meta: dict[str, Any] = {"id": child_id}
            if config.parent_id:
                meta["parent_id"] = config.parent_id
            meta["inheritance_type"] = config.inheritance_type.value
            registry[child_id] = {_META_KEY: meta, "nodes": [], "edges": []}

        pid = config.parent_id
        if pid and pid not in registry:
            registry[pid] = {_META_KEY: {"id": pid}, "nodes": [], "edges": []}

    return registry


def _would_create_circular(config: InheritanceConfig) -> bool:
    """Check if setting this parent would create a circular inheritance.

    Walks the parent chain of ``config.parent_id`` to see if it
    eventually reaches ``config.child_id``.
    """
    target = config.parent_id
    visited: set[str] = set()

    while target:
        if target == config.child_id:
            return True
        if target in visited:
            return True
        visited.add(target)

        cfg = _CONFIG_STORE.get(target)
        target = cfg.parent_id if cfg else None

    return False


def _check_local_element(
    element_id: str,
    graph_id: str,
    graph_data: dict[str, Any],
) -> InheritedElement | None:
    """Check if an element exists locally in a graph (no parent involved)."""
    node_ids = {n["id"] for n in graph_data.get("nodes", []) if "id" in n}
    edge_ids = {e["id"] for e in graph_data.get("edges", []) if "id" in e}

    if element_id in node_ids:
        return InheritedElement(
            element_id=element_id,
            element_type="node",
            source_graph_id=graph_id,
            is_overridden=False,
            local_modifications={},
            depth=0,
        )
    if element_id in edge_ids:
        return InheritedElement(
            element_id=element_id,
            element_type="edge",
            source_graph_id=graph_id,
            is_overridden=False,
            local_modifications={},
            depth=0,
        )
    return None


def _resolve_full_chain(
    child_graph: dict[str, Any],
    parent_graph: dict[str, Any],
) -> dict[str, Any]:
    """Recursively resolve multi-level inheritance.

    Walks from the topmost ancestor down to the child, merging at each level.
    """
    all_graphs = _build_full_registry()

    # Build the ancestor stack from root to direct parent
    ancestors: list[dict[str, Any]] = []
    current = parent_graph
    visited: set[str] = set()

    while True:
        gid = _get_graph_id(current)
        if not gid or gid in visited:
            break
        visited.add(gid)

        ancestors.append(current)

        pid = InheritanceService.get_parent(current)
        if pid is None or pid not in all_graphs:
            break
        current = all_graphs[pid]

    # Reverse: root ancestor first
    ancestors.reverse()

    # Merge ancestors from root to direct parent
    if not ancestors:
        return InheritanceService.resolve_inheritance(
            child_graph, parent_graph, InheritanceType.OVERRIDE
        )

    merged = dict(ancestors[0])
    for ancestor in ancestors[1:]:
        merged = InheritanceService.resolve_inheritance(
            ancestor, merged, InheritanceType.OVERRIDE
        )

    # Finally merge child on top
    merged = InheritanceService.resolve_inheritance(
        child_graph, merged, InheritanceType.OVERRIDE
    )

    return merged
