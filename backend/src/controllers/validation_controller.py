"""Validation Controller — API endpoints for validating graph documents."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from src.services.validation import validate_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validate", tags=["validation"])


@router.post("/graph")
async def validate_graph_endpoint(graph_data: dict[str, Any]):
    report = validate_graph(graph_data)
    return report.to_dict()


@router.post("/dsl")
async def validate_graph_document(graph_data: dict[str, Any]):
    report = validate_graph(graph_data)
    return report.to_dict()
