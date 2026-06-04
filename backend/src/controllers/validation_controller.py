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


@router.post("/{dsl_id}")
async def validate_dsl_graph(
    dsl_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Validate the IR graph for a dsl stored in the database.

    Fetches the complete graph (dsl + nodes + edges) and runs the
    full validation pipeline against it.
    """
    logger.info(f"Validating dsl graph: {dsl_id} (user={current_user.username})")

    from src.repositories.dsl.dsl_attribute_repository import DSLAttributeRepository
    from src.repositories.dsl.dsl_concept_repository import DSLConceptRepository
    from src.repositories.dsl.dsl_edge_repository import DSLEdgeRepository
    from src.repositories.dsl.dsl_repository import DSLRepository
    from src.repositories.dsl.dsl_relation_repository import DSLRelationRepository
    from src.services.dsl.dsl_service import DSLService

    dsl_repo = DSLRepository(db)
    concept_repo = DSLConceptRepository(db)
    attribute_repo = DSLAttributeRepository(db)
    relationship_repo = DSLRelationRepository(db)
    edge_repo = DSLEdgeRepository(db)

    service = DSLService(
        repository=dsl_repo,
        concept_repository=concept_repo,
        attribute_repository=attribute_repo,
        relationship_repository=relationship_repo,
        edge_repository=edge_repo,
    )

    try:
        graph_data = await service.get_dsl_graph(dsl_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching dsl graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dsl graph: {str(e)}",
        )

    # Convert the service response into the standard IR JSON format
    dsl = graph_data["dsl"]
    ir_document: dict[str, Any] = {
        "metadata": {
            "id": dsl.id,
            "name": dsl.name,
            "description": dsl.description,
            "version": dsl.version,
            "status": dsl.status,
            "owner_id": dsl.owner_id,
            "created_at": dsl.created_at.isoformat() if dsl.created_at else None,
            "updated_at": dsl.updated_at.isoformat() if dsl.updated_at else None,
            "node_count": dsl.node_count,
            "edge_count": dsl.edge_count,
            "allowed_node_types": [nt.model_dump() for nt in dsl.allowed_node_types],
            "allowed_edge_types": [et.model_dump() for et in dsl.allowed_edge_types],
        },
        "nodes": graph_data["nodes"],
        "edges": graph_data["edges"],
        "edgeConstraints": graph_data.get("edgeConstraints", []),
    }

    report = validate_graph(ir_document)
    result = report.to_dict()

    if not report.is_valid:
        logger.info(
            f"DSL {dsl_id} validation failed: "
            f"{result['summary']['error_count']} error(s), "
            f"{result['summary']['warning_count']} warning(s)"
        )
    else:
        logger.info(f"DSL {dsl_id} validation passed")

    return result
