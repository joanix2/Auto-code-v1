"""
Pipeline Models — Data models for the code generation pipeline.

Defines the stages, configuration, state, tasks, and requests that flow
through the agent pipeline from prompt to generated code.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ======================================================================
# Pipeline Stages
# ======================================================================


class PipelineStage(str, Enum):
    """All stages in the code generation pipeline, in execution order."""

    PRODUCT_OWNER = "product_owner"
    NER = "ner"
    ONTOLOGIST = "ontologist"
    GRAPH_ENGINEER = "graph_engineer"
    TEMPLATE_ENGINEER = "template_engineer"
    VALIDATOR = "validator"
    REWRITE = "rewrite"
    CODGEN_PLANNER = "codegen_planner"
    GIT_INTEGRATOR = "git_integrator"
    REVIEWER = "reviewer"


# Default execution order for the pipeline
PIPELINE_STAGE_ORDER: list[PipelineStage] = [
    PipelineStage.PRODUCT_OWNER,
    PipelineStage.NER,
    PipelineStage.ONTOLOGIST,
    PipelineStage.GRAPH_ENGINEER,
    PipelineStage.TEMPLATE_ENGINEER,
    PipelineStage.VALIDATOR,
    PipelineStage.REWRITE,
    PipelineStage.CODGEN_PLANNER,
    PipelineStage.GIT_INTEGRATOR,
    PipelineStage.REVIEWER,
]


# ======================================================================
# Error Strategy
# ======================================================================


class PipelineErrorStrategy(str, Enum):
    """Error handling strategy for pipeline execution."""

    ABORT = "abort"  # Stop execution on first error
    SKIP = "skip"  # Skip failed stages, continue with remaining
    RETRY = "retry"  # Retry failed stages


# ======================================================================
# Stage Status
# ======================================================================


class StageStatus(str, Enum):
    """Status of a single pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class PipelineStatus(str, Enum):
    """Overall status of a pipeline run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ======================================================================
# Pipeline Configuration
# ======================================================================


class PipelineConfig(BaseModel):
    """Configuration for a pipeline run."""

    stages: list[PipelineStage] = Field(
        default_factory=lambda: list(PIPELINE_STAGE_ORDER),
        description="Ordered list of stages to execute",
    )
    auto_proceed: bool = Field(
        default=True,
        description="Automatically proceed from one stage to the next",
    )
    error_strategy: PipelineErrorStrategy = Field(
        default=PipelineErrorStrategy.ABORT,
        description="How to handle stage failures",
    )
    max_retries: int = Field(
        default=3, ge=0, description="Maximum retry attempts per stage"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for the pipeline config",
    )


# ======================================================================
# Pipeline State
# ======================================================================


class StageState(BaseModel):
    """Runtime state of a single pipeline stage."""

    stage: PipelineStage
    status: StageStatus = Field(default=StageStatus.PENDING)
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = Field(default=None)
    retry_count: int = Field(default=0, ge=0)


class PipelineState(BaseModel):
    """Runtime state of the entire pipeline."""

    pipeline_id: str = Field(..., description="Unique pipeline identifier")
    status: PipelineStatus = Field(default=PipelineStatus.PENDING)
    config: PipelineConfig = Field(default_factory=PipelineConfig)
    stages: dict[PipelineStage, StageState] = Field(default_factory=dict)
    current_stage: PipelineStage | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Initialize stage states from config stages."""
        if not self.stages:
            self.stages = {
                stage: StageState(stage=stage)
                for stage in self.config.stages
            }


# ======================================================================
# Agent Task
# ======================================================================


class AgentTaskStatus(str, Enum):
    """Status of an individual agent task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentTask(BaseModel):
    """A task assigned to an agent for processing."""

    id: str = Field(..., description="Unique task identifier")
    stage: PipelineStage = Field(..., description="The pipeline stage this task belongs to")
    input_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Input data for the agent",
    )
    output_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Output data produced by the agent",
    )
    status: AgentTaskStatus = Field(default=AgentTaskStatus.PENDING)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ======================================================================
# Generation Request
# ======================================================================


class GenerationRequest(BaseModel):
    """A top-level request to generate code from a prompt."""

    prompt: str = Field(..., min_length=1, description="The user prompt describing what to generate")
    pipeline_config: PipelineConfig = Field(
        default_factory=PipelineConfig,
        description="Pipeline configuration for this request",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata (e.g., project name, user ID)",
    )


# ======================================================================
# Pipeline Summary (for API responses)
# ======================================================================


class PipelineSummary(BaseModel):
    """Summary of a pipeline run, suitable for listing."""

    pipeline_id: str
    status: PipelineStatus
    stage_count: int
    completed_stages: int
    failed_stages: int
    current_stage: PipelineStage | None
    created_at: datetime
    updated_at: datetime
