"""Validation Controller — API endpoints for validating IR graphs.

Endpoints:
- ``POST /api/validate/graph`` — validate an IR graph JSON body.
- ``POST /api/validate/{dsl_id}`` — validate a dsl's graph
  retrieved from the database.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.database import get_db
from src.models.oauth.user import User
from src.services.validation import ValidationReport, validate_graph
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validate", tags=["validation"])


@router.post("/graph")
async def validate_graph_endpoint(
    graph_data: dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Validate an IR graph document sent as JSON body.

    The request body must be a valid IR graph dict with ``metadata``,
    ``nodes``, and ``edges`` keys.

    Returns the validation report including errors, warnings, and a summary.
    """
    logger.info(f"Validating graph (user={current_user.username})")

    report = validate_graph(graph_data)
    result = report.to_dict()

    if not report.is_valid:
        logger.info(
            f"Graph validation failed: {result['summary']['error_count']} error(s), "
            f"{result['summary']['warning_count']} warning(s)"
        )
    else:
        logger.info("Graph validation passed")

    return result


@router.post("/dsl")
async def validate_graph_document(
    graph_data: dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Validate a graph document sent as JSON body.

    The request body should be a dict with ``metadata``, ``nodes``, ``edges`` keys.
    """
    report = validate_graph(graph_data)
    result = report.to_dict()
    logger.info(
        f"Validation: {result['summary']['error_count']} error(s), "
        f"{result['summary']['warning_count']} warning(s)"
    )
    return result
