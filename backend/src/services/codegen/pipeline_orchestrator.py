"""
Pipeline Orchestrator — Manages lifecycle of code generation pipelines.

Provides the core orchestration logic: create, run, cancel, retry stages,
and query pipeline state. Uses in-memory storage for pipeline states.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from .agent_service import BaseAgentService, AGENT_REGISTRY
from .pipeline_models import (
    PIPELINE_STAGE_ORDER,
    PipelineConfig,
    PipelineErrorStrategy,
    PipelineStage,
    PipelineState,
    PipelineStatus,
    StageState,
    StageStatus,
)

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates the execution of code generation pipelines.

    Manages pipeline lifecycle:
    - Create a new pipeline run from config
    - Execute stages sequentially (with optional auto-proceed)
    - Support cancel, retry, and state inspection

    Currently uses in-memory storage (dict). Future versions may persist
    to a database.
    """

    def __init__(self) -> None:
        """Initialize the orchestrator with in-memory storage."""
        self._pipelines: dict[str, PipelineState] = {}

    # ==================================================================
    # Pipeline CRUD
    # ==================================================================

    def create_pipeline(
        self,
        config: PipelineConfig | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PipelineState:
        """Create a new pipeline run.

        Args:
            config: Pipeline configuration (stages, error strategy, etc.).
                Uses defaults if not provided.
            metadata: Optional metadata to attach to the pipeline.

        Returns:
            The new PipelineState.
        """
        pipeline_id = str(uuid.uuid4())
        state = PipelineState(
            pipeline_id=pipeline_id,
            config=config or PipelineConfig(),
            metadata=metadata or {},
        )
        self._pipelines[pipeline_id] = state
        logger.info(f"Created pipeline {pipeline_id}")
        return state

    def get_pipeline_state(self, pipeline_id: str) -> PipelineState | None:
        """Get the current state of a pipeline.

        Args:
            pipeline_id: The pipeline's unique identifier.

        Returns:
            The PipelineState, or None if not found.
        """
        return self._pipelines.get(pipeline_id)

    def list_pipelines(
        self,
        status: PipelineStatus | None = None,
    ) -> list[PipelineState]:
        """List all pipelines, optionally filtered by status.

        Args:
            status: If set, only return pipelines with this status.

        Returns:
            List of PipelineState objects.
        """
        pipelines = list(self._pipelines.values())
        if status:
            pipelines = [p for p in pipelines if p.status == status]
        # Sort by creation time, newest first
        pipelines.sort(key=lambda p: p.created_at, reverse=True)
        return pipelines

    def delete_pipeline(self, pipeline_id: str) -> bool:
        """Delete a pipeline from storage.

        Args:
            pipeline_id: The pipeline to delete.

        Returns:
            True if deleted, False if not found.
        """
        if pipeline_id in self._pipelines:
            del self._pipelines[pipeline_id]
            return True
        return False

    # ==================================================================
    # Pipeline Execution
    # ==================================================================

    def run_pipeline(
        self,
        pipeline_id: str,
    ) -> PipelineState:
        """Execute all stages of a pipeline sequentially.

        Args:
            pipeline_id: The pipeline to execute.

        Returns:
            The final PipelineState after execution.

        Raises:
            ValueError: If the pipeline is not found or not in PENDING state.
        """
        state = self._get_validated_pipeline(pipeline_id, PipelineStatus.PENDING)

        state.status = PipelineStatus.RUNNING
        state.updated_at = datetime.now(timezone.utc)

        stages = state.config.stages
        error_strategy = state.config.error_strategy

        for stage in stages:
            # Check if pipeline was cancelled
            if state.status == PipelineStatus.CANCELLED:
                logger.info(f"Pipeline {pipeline_id} was cancelled, stopping")
                break

            stage_state = state.stages.get(stage)
            if stage_state is None:
                stage_state = StageState(stage=stage)
                state.stages[stage] = stage_state

            if stage_state.status == StageStatus.COMPLETED:
                continue

            state.current_stage = stage

            # Execute the stage
            result = self._execute_stage_internal(state, stage)

            if result.status == StageStatus.FAILED:
                if error_strategy == PipelineErrorStrategy.ABORT:
                    state.status = PipelineStatus.FAILED
                    state.completed_at = datetime.now(timezone.utc)
                    logger.warning(
                        f"Pipeline {pipeline_id} aborted at stage {stage.value}"
                    )
                    return state
                elif error_strategy == PipelineErrorStrategy.SKIP:
                    logger.info(f"Skipping failed stage {stage.value}")
                    continue
                # RETRY is handled within _execute_stage_internal

        # Determine final status
        all_done = all(
            s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED)
            for s in state.stages.values()
        )
        any_failed = any(
            s.status == StageStatus.FAILED for s in state.stages.values()
        )

        if state.status != PipelineStatus.CANCELLED:
            if all_done:
                state.status = PipelineStatus.COMPLETED
            elif any_failed:
                state.status = PipelineStatus.FAILED

        state.current_stage = None
        state.completed_at = datetime.now(timezone.utc)
        state.updated_at = datetime.now(timezone.utc)

        logger.info(
            f"Pipeline {pipeline_id} finished with status {state.status.value}"
        )
        return state

    def run_stage(
        self,
        pipeline_id: str,
        stage: PipelineStage,
    ) -> StageState:
        """Execute a single stage of a pipeline.

        Args:
            pipeline_id: The pipeline identifier.
            stage: The stage to execute.

        Returns:
            The StageState after execution.

        Raises:
            ValueError: If the pipeline is not found.
        """
        state = self._get_validated_pipeline(pipeline_id, None)

        # Allow running if pipeline is PENDING or RUNNING
        if state.status not in (PipelineStatus.PENDING, PipelineStatus.RUNNING):
            raise ValueError(
                f"Cannot run stage on pipeline with status '{state.status.value}'"
            )

        state.status = PipelineStatus.RUNNING
        state.current_stage = stage
        state.updated_at = datetime.now(timezone.utc)

        stage_state = self._execute_stage_internal(state, stage)

        # Check if all remaining stages are done
        stages = state.config.stages
        all_done = all(
            s.status in (StageStatus.COMPLETED, StageStatus.SKIPPED, StageStatus.FAILED)
            for s in state.stages.values()
        )
        if all_done:
            any_failed = any(
                s.status == StageStatus.FAILED for s in state.stages.values()
            )
            state.status = PipelineStatus.FAILED if any_failed else PipelineStatus.COMPLETED
            state.current_stage = None
            state.completed_at = datetime.now(timezone.utc)

        return stage_state

    def retry_stage(
        self,
        pipeline_id: str,
        stage: PipelineStage,
    ) -> StageState:
        """Retry a failed pipeline stage.

        Resets the stage state to PENDING and executes it again.

        Args:
            pipeline_id: The pipeline identifier.
            stage: The stage to retry.

        Returns:
            The StageState after retry.

        Raises:
            ValueError: If pipeline not found, or stage was not failed.
        """
        state = self._get_validated_pipeline(pipeline_id, None)

        stage_state = state.stages.get(stage)
        if stage_state is None:
            raise ValueError(
                f"Stage '{stage.value}' not found in pipeline {pipeline_id}"
            )
        if stage_state.status != StageStatus.FAILED:
            raise ValueError(
                f"Cannot retry stage '{stage.value}': "
                f"current status is '{stage_state.status.value}' "
                f"(expected 'failed')"
            )

        # Reset stage state
        stage_state.status = StageStatus.PENDING
        stage_state.error = None
        stage_state.started_at = None
        stage_state.completed_at = None
        stage_state.result = {}
        state.status = PipelineStatus.RUNNING
        state.updated_at = datetime.now(timezone.utc)

        # Execute
        return self._execute_stage_internal(state, stage)

    def cancel_pipeline(self, pipeline_id: str) -> PipelineState | None:
        """Cancel a running pipeline.

        Args:
            pipeline_id: The pipeline to cancel.

        Returns:
            The updated PipelineState, or None if not found.
        """
        state = self._pipelines.get(pipeline_id)
        if state is None:
            return None

        if state.status in (PipelineStatus.COMPLETED, PipelineStatus.CANCELLED):
            logger.info(
                f"Pipeline {pipeline_id} already in '{state.status.value}' state"
            )
            return state

        state.status = PipelineStatus.CANCELLED
        state.completed_at = datetime.now(timezone.utc)
        state.updated_at = datetime.now(timezone.utc)

        # Mark current and pending stages as cancelled
        for stage_state in state.stages.values():
            if stage_state.status == StageStatus.PENDING:
                stage_state.status = StageStatus.CANCELLED
            elif stage_state.status == StageStatus.RUNNING:
                stage_state.status = StageStatus.CANCELLED

        logger.info(f"Cancelled pipeline {pipeline_id}")
        return state

    # ==================================================================
    # Internal Methods
    # ==================================================================

    def _execute_stage_internal(
        self,
        state: PipelineState,
        stage: PipelineStage,
    ) -> StageState:
        """Execute a stage and update its state.

        Args:
            state: The overall pipeline state.
            stage: The stage to execute.

        Returns:
            The updated StageState.
        """
        stage_state = state.stages.get(stage)
        if stage_state is None:
            stage_state = StageState(stage=stage)
            state.stages[stage] = stage_state

        stage_state.status = StageStatus.RUNNING
        stage_state.started_at = datetime.now(timezone.utc)
        stage_state.retry_count = 0
        state.current_stage = stage
        state.updated_at = datetime.now(timezone.utc)

        agent = AGENT_REGISTRY.get(stage.value)
        if agent is None:
            stage_state.status = StageStatus.FAILED
            stage_state.error = f"No agent registered for stage '{stage.value}'"
            stage_state.completed_at = datetime.now(timezone.utc)
            return stage_state

        # Build input data from accumulated pipeline results
        input_data = self._build_stage_input(state, stage)

        # Execute with retry
        max_retries = state.config.max_retries if state.config.error_strategy == PipelineErrorStrategy.RETRY else 0
        last_error: str | None = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    delay = 1.0 * (2.0 ** (attempt - 1))
                    logger.info(
                        f"Retrying stage '{stage.value}' "
                        f"(attempt {attempt + 1}/{max_retries + 1}) "
                        f"after {delay:.1f}s"
                    )
                    time.sleep(delay)
                    stage_state.retry_count = attempt

                result = agent.process(input_data)

                if not result.get("success", True):
                    raise RuntimeError(result.get("error", "Agent returned failure"))

                stage_state.status = StageStatus.COMPLETED
                stage_state.result = result
                stage_state.error = None
                stage_state.completed_at = datetime.now(timezone.utc)
                state.updated_at = datetime.now(timezone.utc)

                logger.info(f"Stage '{stage.value}' completed successfully")
                return stage_state

            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    f"Stage '{stage.value}' attempt {attempt + 1} failed: {last_error}"
                )
                if attempt < max_retries:
                    continue
                # Exhausted retries
                stage_state.status = StageStatus.FAILED
                stage_state.error = last_error
                stage_state.completed_at = datetime.now(timezone.utc)
                state.updated_at = datetime.now(timezone.utc)

                logger.error(f"Stage '{stage.value}' failed after {attempt + 1} attempt(s)")
                return stage_state

        # Should not reach here, but safeguard
        stage_state.status = StageStatus.FAILED
        stage_state.error = last_error or "Unknown error"
        stage_state.completed_at = datetime.now(timezone.utc)
        return stage_state

    def _build_stage_input(
        self,
        state: PipelineState,
        stage: PipelineStage,
    ) -> dict[str, Any]:
        """Build the input data for a stage from accumulated pipeline results.

        Collects outputs from all previously completed stages and merges
        them into a single input dict for the requested stage.

        Args:
            state: The pipeline state with completed stage results.
            stage: The target stage to build input for.

        Returns:
            Input data dict for the agent.
        """
        input_data: dict[str, Any] = {}

        # Include metadata keys at the top level so agents can access them
        # directly (e.g., input_data["prompt"] instead of input_data["metadata"]["prompt"])
        for key, value in state.metadata.items():
            input_data[key] = value

        # Collect all previous stage results
        for prev_stage in PIPELINE_STAGE_ORDER:
            if prev_stage == stage:
                break
            stage_state = state.stages.get(prev_stage)
            if stage_state and stage_state.status == StageStatus.COMPLETED:
                result = stage_state.result
                for key, value in result.items():
                    if key != "success":
                        input_data[key] = value

        return input_data

    def _get_validated_pipeline(
        self,
        pipeline_id: str,
        expected_status: PipelineStatus | None,
    ) -> PipelineState:
        """Get and validate a pipeline exists and optionally has a given status.

        Args:
            pipeline_id: Pipeline identifier.
            expected_status: If set, validate pipeline has this status.

        Returns:
            The PipelineState.

        Raises:
            ValueError: If pipeline not found or status mismatch.
        """
        state = self._pipelines.get(pipeline_id)
        if state is None:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")

        if expected_status is not None and state.status != expected_status:
            raise ValueError(
                f"Pipeline '{pipeline_id}' has status '{state.status.value}', "
                f"expected '{expected_status.value}'"
            )

        return state
