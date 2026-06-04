"""Rewrite Controller — REST API endpoints for graph rewriting.

Endpoints:
- ``GET  /api/rewrite/rules``   — list registered rules.
- ``POST /api/rewrite/apply``   — apply rules (single or all) to a graph.
- ``POST /api/rewrite/fixpoint``— apply rules until fixpoint.
- ``POST /api/rewrite/match``   — find pattern matches in a graph.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query, status

from src.services.rewrite import DEFAULT_RULES, RewriteEngine, match_pattern

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rewrite", tags=["rewrite"])

# ---------------------------------------------------------------------------
# Global engine instance with default rules
# ---------------------------------------------------------------------------

_engine = RewriteEngine()
_engine.register_rules(DEFAULT_RULES)


def get_engine() -> RewriteEngine:
    """Return the global rewrite engine (can be overridden in tests)."""
    return _engine


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/rules")
async def list_rules():
    """List all registered rewrite rules with their metadata."""
    engine = get_engine()
    rules = engine.list_rules()
    return {"count": len(rules), "rules": rules}


@router.post("/apply")
async def apply_rules(
    graph_data: dict[str, Any] = Body(..., description="IR graph document"),
    rule_name: str | None = Query(
        None, description="Optional: apply only this named rule"
    ),
):
    """Apply rewrite rules to a graph document.

    If ``rule_name`` is provided, only that single rule is applied.
    Otherwise, all enabled rules are applied once in priority order.
    """
    engine = get_engine()

    if rule_name:
        result = engine.apply_rule(rule_name, graph_data)
    else:
        result = engine.apply_all(graph_data)

    if not result.success and result.errors:
        logger.warning("Rewrite failed: %s", result.errors)

    return {
        "success": result.success,
        "applied_rules": result.applied_rules,
        "errors": result.errors,
        "graph": result.modified_graph,
    }


@router.post("/fixpoint")
async def apply_fixpoint(
    graph_data: dict[str, Any] = Body(..., description="IR graph document"),
    max_iterations: int = Query(
        10, ge=1, le=100, description="Maximum fixpoint iterations"
    ),
):
    """Apply rewrite rules repeatedly until no rule changes the graph.

    The loop stops when a full pass of all rules results in no changes,
    or when *max_iterations* is reached.
    """
    engine = get_engine()
    result = engine.apply_fixpoint(graph_data, max_iterations=max_iterations)

    if not result.success:
        logger.warning("Fixpoint did not converge: %s", result.errors)

    return {
        "success": result.success,
        "applied_rules": result.applied_rules,
        "iteration_count": result.iteration_count,
        "errors": result.errors,
        "graph": result.modified_graph,
    }


@router.post("/match")
async def find_pattern(
    graph_data: dict[str, Any] = Body(..., description="IR graph document"),
    pattern: dict[str, Any] = Body(..., description="Pattern specification"),
):
    """Find subgraphs matching a structural pattern.

    Pattern format::

        {
            "nodes": {
                "alias_a": {"type": "concept"},
                "alias_b": {"type": "attribute"}
            },
            "edges": [
                {"source": "alias_a", "target": "alias_b", "type": "HAS_ATTRIBUTE"}
            ]
        }

    Returns a list of matches, each mapping alias → node data.
    """
    try:
        matches = match_pattern(graph_data, pattern)
        return {"count": len(matches), "matches": matches}
    except Exception as exc:
        logger.exception("Pattern matching failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pattern matching error: {exc}",
        )
