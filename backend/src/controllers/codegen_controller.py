"""
Codegen Controller — REST API endpoints for the code generation pipeline.

Provides:
- POST /api/codegen/pipeline — create and optionally run a pipeline
- GET /api/codegen/pipeline/{pipeline_id} — get pipeline state
- POST /api/codegen/pipeline/{pipeline_id}/cancel — cancel a pipeline
- POST /api/codegen/pipeline/{pipeline_id}/retry/{stage} — retry a stage
- GET /api/codegen/pipelines — list all pipelines
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from src.services.codegen import (
    PIPELINE_STAGE_ORDER,
    PipelineConfig,
    PipelineErrorStrategy,
    PipelineOrchestrator,
    PipelineStage,
    PipelineStatus,
    PipelineSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/codegen", tags=["codegen"])

# ------------------------------------------------------------------
# Global orchestrator instance (singleton-like)
# ------------------------------------------------------------------

_orchestrator: PipelineOrchestrator | None = None


def get_orchestrator() -> PipelineOrchestrator:
    """Get or create the global PipelineOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator


# ======================================================================
# Endpoints
# ======================================================================


@router.post("/pipeline", status_code=status.HTTP_201_CREATED)
async def create_pipeline(data: dict[str, Any]):
    """Create and optionally run a code generation pipeline.

    Request body:
        prompt (str, optional): The generation prompt.
        auto_run (bool, optional): If true, execute immediately (default: false).
        stages (list[str], optional): Ordered stage names. Uses default order if omitted.
        error_strategy (str, optional): 'abort', 'skip', or 'retry'.
        metadata (dict, optional): Pipeline metadata.

    Returns:
        Pipeline state with pipeline_id.
    """
    try:
        # Build pipeline config
        stage_names = data.get("stages")
        stages = None
        if stage_names:
            stages = []
            for name in stage_names:
                try:
                    stages.append(PipelineStage(name))
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown stage '{name}'. Valid stages: {[s.value for s in PipelineStage]}",
                    )

        error_strategy_name = data.get("error_strategy", "abort")
        try:
            error_strategy = PipelineErrorStrategy(error_strategy_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown error_strategy '{error_strategy_name}'. "
                       f"Valid values: {[s.value for s in PipelineErrorStrategy]}",
            )

        config = PipelineConfig(
            stages=stages or list(PIPELINE_STAGE_ORDER),
            error_strategy=error_strategy,
            auto_proceed=data.get("auto_proceed", True),
        )

        metadata = data.get("metadata", {})

        # Optionally attach the prompt
        if "prompt" in data:
            metadata["prompt"] = data["prompt"]

        orchestrator = get_orchestrator()
        state = orchestrator.create_pipeline(config=config, metadata=metadata)

        # Auto-run if requested
        auto_run = data.get("auto_run", False)
        if auto_run:
            state = orchestrator.run_pipeline(state.pipeline_id)

        return _pipeline_to_response(state)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pipeline: {e}",
        )


@router.get("/pipelines")
async def list_pipelines(
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
):
    """List all pipelines, optionally filtered by status.

    Args:
        status_filter: Optional status filter (pending, running, completed, failed, cancelled).

    Returns:
        List of pipeline summaries.
    """
    orchestrator = get_orchestrator()

    status_enum = None
    if status_filter:
        try:
            status_enum = PipelineStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown status '{status_filter}'. "
                       f"Valid values: {[s.value for s in PipelineStatus]}",
            )

    pipelines = orchestrator.list_pipelines(status=status_enum)
    summaries = [_pipeline_summary(p) for p in pipelines]

    return {
        "pipelines": summaries,
        "count": len(summaries),
    }


@router.get("/pipeline/{pipeline_id}")
async def get_pipeline(pipeline_id: str = Path(..., description="Pipeline ID")):
    """Get the current state of a pipeline.

    Args:
        pipeline_id: The pipeline's unique identifier.

    Returns:
        Pipeline state with all stage details.
    """
    orchestrator = get_orchestrator()
    state = orchestrator.get_pipeline_state(pipeline_id)

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline '{pipeline_id}' not found",
        )

    return _pipeline_to_response(state)


@router.post("/pipeline/{pipeline_id}/cancel")
async def cancel_pipeline(pipeline_id: str = Path(..., description="Pipeline ID")):
    """Cancel a running pipeline.

    Args:
        pipeline_id: The pipeline to cancel.

    Returns:
        Updated pipeline state.
    """
    orchestrator = get_orchestrator()
    state = orchestrator.cancel_pipeline(pipeline_id)

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline '{pipeline_id}' not found",
        )

    return _pipeline_to_response(state)


@router.post("/pipeline/{pipeline_id}/retry/{stage}")
async def retry_stage(
    pipeline_id: str = Path(..., description="Pipeline ID"),
    stage: str = Path(..., description="Stage name to retry"),
):
    """Retry a failed pipeline stage.

    Args:
        pipeline_id: The pipeline identifier.
        stage: The stage name to retry (e.g., 'ner', 'validator').

    Returns:
        Updated pipeline state.
    """
    orchestrator = get_orchestrator()

    # Validate stage name
    try:
        stage_enum = PipelineStage(stage)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown stage '{stage}'. Valid stages: {[s.value for s in PipelineStage]}",
        )

    try:
        stage_state = orchestrator.retry_stage(pipeline_id, stage_enum)
        return _pipeline_to_response(
            orchestrator.get_pipeline_state(pipeline_id)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


# ======================================================================
# Internal helpers
# ======================================================================


def _pipeline_to_response(state: PipelineState) -> dict[str, Any]:
    """Convert a PipelineState to a JSON-serializable response dict."""
    return {
        "pipeline_id": state.pipeline_id,
        "status": state.status.value,
        "current_stage": state.current_stage.value if state.current_stage else None,
        "stages": [
            {
                "stage": ss.stage.value,
                "status": ss.status.value,
                "started_at": ss.started_at.isoformat() if ss.started_at else None,
                "completed_at": ss.completed_at.isoformat() if ss.completed_at else None,
                "error": ss.error,
                "retry_count": ss.retry_count,
                "result_summary": ss.result.get("summary") if ss.result else None,
            }
            for ss in state.stages.values()
        ],
        "stage_count": len(state.stages),
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
        "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        "metadata": state.metadata,
    }


def _pipeline_summary(state: PipelineState) -> dict[str, Any]:
    """Create a summary dict for a pipeline."""
    completed = sum(
        1 for s in state.stages.values()
        if s.status.value in ("completed", "skipped")
    )
    failed = sum(
        1 for s in state.stages.values()
        if s.status.value == "failed"
    )
    return {
        "pipeline_id": state.pipeline_id,
        "status": state.status.value,
        "stage_count": len(state.stages),
        "completed_stages": completed,
        "failed_stages": failed,
        "current_stage": state.current_stage.value if state.current_stage else None,
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
    }
