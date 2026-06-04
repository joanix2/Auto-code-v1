"""
Codegen Service — Agent pipeline orchestrator for code generation.

Provides:
- Pipeline models (stages, config, state, tasks)
- Agent service interfaces and mock implementations
- Pipeline orchestration (create, run, cancel, retry)

Usage::

    from src.services.codegen import (
        PipelineOrchestrator,
        PipelineConfig,
        PipelineStage,
        GenerationRequest,
        get_agent,
    )

    orch = PipelineOrchestrator()
    state = orch.create_pipeline()
    state = orch.run_pipeline(state.pipeline_id)
"""

from __future__ import annotations

from .agent_service import (
    AGENT_REGISTRY,
    BaseAgentService,
    CodegenPlannerAgent,
    GitIntegratorAgent,
    GraphEngineerAgent,
    NERAgent,
    OntologistAgent,
    ProductOwnerAgent,
    ReviewerAgent,
    RewriteAgent,
    TemplateEngineerAgent,
    ValidatorAgent,
    get_agent,
)
from .pipeline_models import (
    PIPELINE_STAGE_ORDER,
    AgentTask,
    AgentTaskStatus,
    GenerationRequest,
    PipelineConfig,
    PipelineErrorStrategy,
    PipelineStage,
    PipelineState,
    PipelineStatus,
    PipelineSummary,
    StageState,
    StageStatus,
)
from .pipeline_orchestrator import PipelineOrchestrator

__all__ = [
    # Pipeline models
    "PipelineStage",
    "PipelineConfig",
    "PipelineErrorStrategy",
    "PipelineState",
    "PipelineStatus",
    "StageStatus",
    "StageState",
    "AgentTask",
    "AgentTaskStatus",
    "GenerationRequest",
    "PipelineSummary",
    "PIPELINE_STAGE_ORDER",
    # Agent services
    "BaseAgentService",
    "ProductOwnerAgent",
    "NERAgent",
    "OntologistAgent",
    "GraphEngineerAgent",
    "TemplateEngineerAgent",
    "ValidatorAgent",
    "RewriteAgent",
    "CodegenPlannerAgent",
    "GitIntegratorAgent",
    "ReviewerAgent",
    "AGENT_REGISTRY",
    "get_agent",
    # Orchestrator
    "PipelineOrchestrator",
]
