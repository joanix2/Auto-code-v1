"""Validation Controller — API endpoints for validating IR graphs.

Endpoints:
- ``POST /api/validate/graph`` — validate an IR graph JSON body.
- ``POST /api/validate/{metamodel_id}`` — validate a metamodel's graph
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


@router.post("/{metamodel_id}")
async def validate_metamodel_graph(
    metamodel_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """Validate the IR graph for a metamodel stored in the database.

    Fetches the complete graph (metamodel + nodes + edges) and runs the
    full validation pipeline against it.
    """
    from src.repositories.MDE.M2.attribute_repository import AttributeRepository
    from src.repositories.MDE.M2.concept_repository import ConceptRepository
    from src.repositories.MDE.M2.metamodel_edge_repository import MetamodelEdgeRepository
    from src.repositories.MDE.M2.metamodel_repository import MetamodelRepository
    from src.repositories.MDE.M2.relationship_repository import RelationshipRepository
    from src.services.MDE.M2.metamodel_service import MetamodelService

    logger.info(f"Validating metamodel graph: {metamodel_id} (user={current_user.username})")

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
        edge_repository=edge_repo,
    )

    try:
        graph_data = await service.get_metamodel_with_graph(metamodel_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching metamodel graph: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metamodel graph: {str(e)}",
        )

    # Convert the service response into the standard IR JSON format
    metamodel = graph_data["metamodel"]
    ir_document: dict[str, Any] = {
        "metadata": {
            "id": metamodel.id,
            "name": metamodel.name,
            "description": metamodel.description,
            "version": metamodel.version,
            "status": metamodel.status,
            "owner_id": metamodel.owner_id,
            "created_at": metamodel.created_at.isoformat() if metamodel.created_at else None,
            "updated_at": metamodel.updated_at.isoformat() if metamodel.updated_at else None,
            "node_count": metamodel.node_count,
            "edge_count": metamodel.edge_count,
            "allowed_node_types": [nt.model_dump() for nt in metamodel.allowed_node_types],
            "allowed_edge_types": [et.model_dump() for et in metamodel.allowed_edge_types],
        },
        "nodes": graph_data["nodes"],
        "edges": graph_data["edges"],
        "edgeConstraints": graph_data.get("edgeConstraints", []),
    }

    report = validate_graph(ir_document)
    result = report.to_dict()

    if not report.is_valid:
        logger.info(
            f"Metamodel {metamodel_id} validation failed: "
            f"{result['summary']['error_count']} error(s), "
            f"{result['summary']['warning_count']} warning(s)"
        )
    else:
        logger.info(f"Metamodel {metamodel_id} validation passed")

    return result
