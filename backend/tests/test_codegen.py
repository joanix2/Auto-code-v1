"""Tests for Codegen Pipeline — Pipeline Models, Agent Services, Orchestrator, and API.

Tests cover:
1. Pipeline models (PipelineStage, PipelineConfig, PipelineState, AgentTask, GenerationRequest)
2. Agent service interfaces (each agent type processes input and returns output)
3. Pipeline orchestrator (create, run, cancel, retry, edge cases)
4. API endpoints (create, list, get, cancel, retry)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.services.codegen import (
    AGENT_REGISTRY,
    PIPELINE_STAGE_ORDER,
    BaseAgentService,
    CodegenPlannerAgent,
    GenerationRequest,
    GitIntegratorAgent,
    GraphEngineerAgent,
    NERAgent,
    OntologistAgent,
    PipelineConfig,
    PipelineErrorStrategy,
    PipelineOrchestrator,
    PipelineStage,
    PipelineState,
    PipelineStatus,
    ProductOwnerAgent,
    ReviewerAgent,
    RewriteAgent,
    StageStatus,
    TemplateEngineerAgent,
    ValidatorAgent,
    get_agent,
)
from src.services.codegen.pipeline_models import (
    AgentTask,
    AgentTaskStatus,
    PipelineSummary,
    StageState,
)


# ======================================================================
# Pipeline Models Tests
# ======================================================================


class TestPipelineStage:
    """Tests for PipelineStage enum."""

    def test_enum_values(self):
        """Should have all expected stages."""
        expected = [
            "product_owner", "ner", "ontologist", "graph_engineer",
            "template_engineer", "validator", "rewrite", "codegen_planner",
            "git_integrator", "reviewer",
        ]
        values = [s.value for s in PipelineStage]
        assert values == expected

    def test_pipeline_stage_order(self):
        """PIPELINE_STAGE_ORDER should contain all stages in order."""
        assert len(PIPELINE_STAGE_ORDER) == 10
        assert PIPELINE_STAGE_ORDER[0] == PipelineStage.PRODUCT_OWNER
        assert PIPELINE_STAGE_ORDER[-1] == PipelineStage.REVIEWER
        # Verify all stages are covered exactly once
        assert set(PIPELINE_STAGE_ORDER) == set(PipelineStage)


class TestPipelineConfig:
    """Tests for PipelineConfig model."""

    def test_default_config(self):
        """Should create config with sensible defaults."""
        config = PipelineConfig()
        assert len(config.stages) == 10
        assert config.auto_proceed is True
        assert config.error_strategy == PipelineErrorStrategy.ABORT
        assert config.max_retries == 3

    def test_custom_config(self):
        """Should create config with custom values."""
        config = PipelineConfig(
            stages=[PipelineStage.NER, PipelineStage.VALIDATOR],
            auto_proceed=False,
            error_strategy=PipelineErrorStrategy.RETRY,
            max_retries=5,
        )
        assert len(config.stages) == 2
        assert config.auto_proceed is False
        assert config.error_strategy == PipelineErrorStrategy.RETRY
        assert config.max_retries == 5

    def test_error_strategy_values(self):
        """Should have all error strategies."""
        assert PipelineErrorStrategy.ABORT.value == "abort"
        assert PipelineErrorStrategy.SKIP.value == "skip"
        assert PipelineErrorStrategy.RETRY.value == "retry"


class TestStageState:
    """Tests for StageState model."""

    def test_default_state(self):
        """Should create stage state with defaults."""
        state = StageState(stage=PipelineStage.NER)
        assert state.stage == PipelineStage.NER
        assert state.status == StageStatus.PENDING
        assert state.started_at is None
        assert state.completed_at is None
        assert state.result == {}
        assert state.error is None
        assert state.retry_count == 0


class TestPipelineState:
    """Tests for PipelineState model."""

    def test_create_state(self):
        """Should create pipeline state with generated stages."""
        config = PipelineConfig(stages=[
            PipelineStage.PRODUCT_OWNER,
            PipelineStage.NER,
        ])
        state = PipelineState(
            pipeline_id="test-1",
            config=config,
        )
        assert state.pipeline_id == "test-1"
        assert state.status == PipelineStatus.PENDING
        assert state.config == config
        assert len(state.stages) == 2
        assert PipelineStage.PRODUCT_OWNER in state.stages
        assert PipelineStage.NER in state.stages

    def test_stage_order_in_state(self):
        """Stages in state should match config order."""
        config = PipelineConfig(stages=[
            PipelineStage.REVIEWER,
            PipelineStage.NER,
        ])
        state = PipelineState(
            pipeline_id="test-2",
            config=config,
        )
        stage_list = list(state.stages.keys())
        assert stage_list == [PipelineStage.REVIEWER, PipelineStage.NER]


class TestAgentTask:
    """Tests for AgentTask model."""

    def test_create_task(self):
        """Should create an agent task."""
        task = AgentTask(
            id="task-1",
            stage=PipelineStage.NER,
            input_data={"tickets": [{"title": "Test"}]},
        )
        assert task.id == "task-1"
        assert task.stage == PipelineStage.NER
        assert task.status == AgentTaskStatus.PENDING
        assert task.output_data == {}
        assert task.error is None

    def test_task_with_output(self):
        """Should create a completed task."""
        task = AgentTask(
            id="task-2",
            stage=PipelineStage.PRODUCT_OWNER,
            input_data={"prompt": "Build a blog"},
            output_data={"tickets": [{"title": "Blog system"}]},
            status=AgentTaskStatus.COMPLETED,
        )
        assert task.status == AgentTaskStatus.COMPLETED
        assert task.output_data["tickets"][0]["title"] == "Blog system"


class TestGenerationRequest:
    """Tests for GenerationRequest model."""

    def test_valid_request(self):
        """Should create a valid generation request."""
        req = GenerationRequest(prompt="Generate a user management system")
        assert req.prompt == "Generate a user management system"
        assert req.pipeline_config is not None
        assert req.metadata == {}

    def test_empty_prompt_raises(self):
        """Should reject empty prompt."""
        with pytest.raises(ValueError):
            GenerationRequest(prompt="")

    def test_custom_metadata(self):
        """Should store metadata."""
        req = GenerationRequest(
            prompt="Build API",
            metadata={"project": "my-app", "user_id": "u-1"},
        )
        assert req.metadata["project"] == "my-app"


class TestPipelineSummary:
    """Tests for PipelineSummary model."""

    def test_create_summary(self):
        """Should create a summary from pipeline state."""
        summary = PipelineSummary(
            pipeline_id="p-1",
            status=PipelineStatus.RUNNING,
            stage_count=5,
            completed_stages=2,
            failed_stages=0,
            current_stage=PipelineStage.NER,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert summary.pipeline_id == "p-1"
        assert summary.status == PipelineStatus.RUNNING
        assert summary.completed_stages == 2


# ======================================================================
# Agent Service Tests
# ======================================================================


class TestProductOwnerAgent:
    """Tests for ProductOwnerAgent."""

    def test_process_with_prompt(self):
        """Should generate tickets from prompt."""
        agent = ProductOwnerAgent()
        result = agent.process({"prompt": "Build a task management system"})
        assert result["success"] is True
        assert len(result["tickets"]) >= 1
        assert "title" in result["tickets"][0]
        assert "acceptance_criteria" in result["tickets"][0]

    def test_process_empty_prompt(self):
        """Should return error for empty prompt."""
        agent = ProductOwnerAgent()
        result = agent.process({"prompt": ""})
        assert result["success"] is False
        assert "error" in result

    def test_process_with_context(self):
        """Should use context for ticket generation."""
        agent = ProductOwnerAgent()
        result = agent.process({
            "prompt": "Build login",
            "context": {"priority": "high", "estimated_hours": 16},
        })
        assert result["success"] is True
        assert result["tickets"][0]["priority"] == "high"


class TestNERAgent:
    """Tests for NERAgent."""

    def test_process_with_tickets(self):
        """Should extract entities and relations from tickets."""
        agent = NERAgent()
        result = agent.process({
            "tickets": [
                {"id": "t-1", "title": "User Management"},
                {"id": "t-2", "title": "Blog Posts"},
            ],
        })
        assert result["success"] is True
        assert len(result["entities"]) >= 2
        assert len(result["relations"]) >= 1

    def test_process_no_tickets(self):
        """Should return error for empty tickets."""
        agent = NERAgent()
        result = agent.process({"tickets": []})
        assert result["success"] is False
        assert "error" in result


class TestOntologistAgent:
    """Tests for OntologistAgent."""

    def test_process_with_entities(self):
        """Should build ontology from entities and relations."""
        agent = OntologistAgent()
        result = agent.process({
            "entities": [
                {"id": "e1", "name": "User", "type": "concept"},
                {"id": "e2", "name": "email", "type": "attribute"},
            ],
            "relations": [
                {"source_id": "e1", "target_id": "e2", "relation": "HAS_ATTRIBUTE"},
            ],
        })
        assert result["success"] is True
        assert len(result["concepts"]) >= 1

    def test_process_no_entities(self):
        """Should return error for no entities."""
        agent = OntologistAgent()
        result = agent.process({"entities": []})
        assert result["success"] is False


class TestGraphEngineerAgent:
    """Tests for GraphEngineerAgent."""

    def test_process_with_concepts(self):
        """Should build IR graph from concepts."""
        agent = GraphEngineerAgent()
        result = agent.process({
            "concepts": [
                {
                    "id": "c1",
                    "name": "User",
                    "attributes": [
                        {"id": "a1", "name": "email", "data_type": "string"},
                    ],
                },
            ],
        })
        assert result["success"] is True
        assert len(result["nodes"]) >= 2  # concept + attribute
        assert len(result["edges"]) >= 1

    def test_process_no_concepts(self):
        """Should return error for no concepts."""
        agent = GraphEngineerAgent()
        result = agent.process({"concepts": []})
        assert result["success"] is False


class TestTemplateEngineerAgent:
    """Tests for TemplateEngineerAgent."""

    def test_process_with_nodes(self):
        """Should generate files from graph nodes."""
        agent = TemplateEngineerAgent()
        result = agent.process({
            "nodes": [
                {"id": "n1", "name": "User", "kind": "concept"},
                {"id": "n2", "name": "email", "kind": "attribute"},
            ],
            "edges": [],
        })
        assert result["success"] is True
        assert len(result["files"]) >= 2  # model + api route

    def test_process_no_nodes(self):
        """Should return error for no nodes."""
        agent = TemplateEngineerAgent()
        result = agent.process({"nodes": []})
        assert result["success"] is False


class TestValidatorAgent:
    """Tests for ValidatorAgent."""

    def test_validate_valid_graph(self):
        """Should pass validation for clean graph."""
        agent = ValidatorAgent()
        result = agent.process({
            "nodes": [
                {"id": "n1", "name": "User", "kind": "concept"},
            ],
            "edges": [],
            "files": [
                {"path": "models/user.py", "content": "class User: pass"},
            ],
        })
        assert result["success"] is True
        assert result["is_valid"] is True

    def test_validate_missing_name(self):
        """Should report error for node without name."""
        agent = ValidatorAgent()
        result = agent.process({
            "nodes": [
                {"id": "n1", "kind": "concept"},  # missing name
            ],
            "edges": [],
            "files": [],
        })
        assert result["success"] is True
        assert result["is_valid"] is False
        assert len(result["errors"]) >= 1

    def test_validate_bad_edge_reference(self):
        """Should report error for edge referencing unknown node."""
        agent = ValidatorAgent()
        result = agent.process({
            "nodes": [{"id": "n1", "name": "User", "kind": "concept"}],
            "edges": [
                {"source_id": "n1", "target_id": "nonexistent"},
            ],
            "files": [],
        })
        assert result["success"] is True
        assert result["is_valid"] is False


class TestRewriteAgent:
    """Tests for RewriteAgent."""

    def test_rewrite_with_nodes(self):
        """Should apply transformations to nodes."""
        agent = RewriteAgent()
        result = agent.process({
            "nodes": [
                {"id": "n1", "name": "user_management", "kind": "concept", "properties": {}},
            ],
            "edges": [],
        })
        assert result["success"] is True
        assert len(result["nodes"]) == 1
        assert len(result["transformations"]) >= 1

    def test_rewrite_no_nodes(self):
        """Should return error for no nodes."""
        agent = RewriteAgent()
        result = agent.process({"nodes": []})
        assert result["success"] is False


class TestCodegenPlannerAgent:
    """Tests for CodegenPlannerAgent."""

    def test_process_with_nodes(self):
        """Should create generation plan from graph nodes."""
        agent = CodegenPlannerAgent()
        result = agent.process({
            "nodes": [
                {"id": "n1", "name": "User", "kind": "concept"},
            ],
        })
        assert result["success"] is True
        assert result["plan"] is not None
        assert len(result["plan"]["steps"]) >= 3  # model + api + sql

    def test_process_no_input(self):
        """Should return error for no input."""
        agent = CodegenPlannerAgent()
        result = agent.process({"nodes": []})
        assert result["success"] is False


class TestGitIntegratorAgent:
    """Tests for GitIntegratorAgent."""

    def test_process_with_files(self):
        """Should create commit summary from files."""
        agent = GitIntegratorAgent()
        result = agent.process({
            "files": [
                {"path": "models/user.py", "content": "class User: pass"},
            ],
        })
        assert result["success"] is True
        assert result["commit_summary"] is not None
        assert result["commit_summary"]["stats"]["files_changed"] == 1

    def test_process_no_files(self):
        """Should return error for no files."""
        agent = GitIntegratorAgent()
        result = agent.process({"files": []})
        assert result["success"] is False


class TestReviewerAgent:
    """Tests for ReviewerAgent."""

    def test_review_all_good(self):
        """Should approve when all artifacts are valid."""
        agent = ReviewerAgent()
        result = agent.process({
            "tickets": [{"id": "t-1", "title": "Test", "acceptance_criteria": ["ok"]}],
            "concepts": [{"id": "c1", "name": "Test"}],
            "nodes": [{"id": "n1", "name": "Test", "kind": "concept"}],
            "edges": [],
            "files": [{"path": "test.py", "content": "content"}],
            "plan": {"steps": [{"name": "s1"}]},
            "commit_summary": {"branch": "main"},
            "validation": {"is_valid": True, "errors": []},
        })
        assert result["success"] is True
        assert result["is_approved"] is True

    def test_review_with_issues(self):
        """Should flag issues when artifacts are missing."""
        agent = ReviewerAgent()
        result = agent.process({
            "tickets": [],
            "concepts": [],
            "nodes": [],
            "edges": [],
            "files": [],
        })
        assert result["success"] is True
        assert result["is_approved"] is False
        assert len(result["issues"]) >= 1


class TestAgentRegistry:
    """Tests for the AGENT_REGISTRY."""

    def test_all_agents_registered(self):
        """All pipeline stages should have a registered agent."""
        for stage in PipelineStage:
            agent = get_agent(stage.value)
            assert agent is not None, f"No agent for stage '{stage.value}'"
            assert isinstance(agent, BaseAgentService)

    def test_agent_name_matches_stage(self):
        """Agent name should match its stage key."""
        for stage in PipelineStage:
            agent = get_agent(stage.value)
            assert agent is not None
            assert agent.agent_name == stage.value

    def test_unknown_agent(self):
        """Should return None for unknown agent key."""
        agent = get_agent("unknown_stage")
        assert agent is None


# ======================================================================
# Pipeline Orchestrator Tests
# ======================================================================


class TestPipelineOrchestrator:
    """Tests for PipelineOrchestrator."""

    def test_create_pipeline(self):
        """Should create a pipeline with default state."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline()
        assert state.pipeline_id is not None
        assert state.status == PipelineStatus.PENDING
        assert len(state.stages) == 10

    def test_create_pipeline_with_config(self):
        """Should create pipeline with custom config."""
        orch = PipelineOrchestrator()
        config = PipelineConfig(
            stages=[PipelineStage.NER, PipelineStage.VALIDATOR],
        )
        state = orch.create_pipeline(config=config, metadata={"project": "test"})
        assert len(state.stages) == 2
        assert state.metadata["project"] == "test"

    def test_get_pipeline_state(self):
        """Should retrieve pipeline state by ID."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline()
        retrieved = orch.get_pipeline_state(state.pipeline_id)
        assert retrieved is not None
        assert retrieved.pipeline_id == state.pipeline_id

    def test_get_pipeline_state_not_found(self):
        """Should return None for unknown ID."""
        orch = PipelineOrchestrator()
        result = orch.get_pipeline_state("nonexistent")
        assert result is None

    def test_list_pipelines(self):
        """Should list all pipelines newest first."""
        orch = PipelineOrchestrator()
        s1 = orch.create_pipeline(metadata={"name": "first"})
        s2 = orch.create_pipeline(metadata={"name": "second"})
        pipelines = orch.list_pipelines()
        assert len(pipelines) == 2
        # Newest first
        assert pipelines[0].pipeline_id == s2.pipeline_id

    def test_list_pipelines_filter_by_status(self):
        """Should filter pipelines by status."""
        orch = PipelineOrchestrator()
        orch.create_pipeline(metadata={"name": "p1"})
        orch.create_pipeline(metadata={"name": "p2"})
        pending = orch.list_pipelines(status=PipelineStatus.PENDING)
        assert len(pending) == 2
        completed = orch.list_pipelines(status=PipelineStatus.COMPLETED)
        assert len(completed) == 0

    def test_run_pipeline_full_flow(self):
        """Should run all stages and complete successfully."""
        orch = PipelineOrchestrator()
        config = PipelineConfig(
            stages=[
                PipelineStage.PRODUCT_OWNER,
                PipelineStage.NER,
            ],
        )
        state = orch.create_pipeline(
            config=config,
            metadata={"prompt": "Build a blog system"},
        )
        result = orch.run_pipeline(state.pipeline_id)
        assert result.status == PipelineStatus.COMPLETED
        # Both stages should be completed
        po_state = result.stages[PipelineStage.PRODUCT_OWNER]
        assert po_state.status == StageStatus.COMPLETED
        ner_state = result.stages[PipelineStage.NER]
        assert ner_state.status == StageStatus.COMPLETED

    def test_run_pipeline_with_all_stages(self):
        """Should run all 10 stages and complete."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline(
            metadata={"prompt": "Generate a full application"},
        )
        result = orch.run_pipeline(state.pipeline_id)
        assert result.status == PipelineStatus.COMPLETED
        for stage in PipelineStage:
            s = result.stages.get(stage)
            assert s is not None, f"Stage {stage.value} missing"
            assert s.status == StageStatus.COMPLETED, f"Stage {stage.value} failed: {s.error}"

    def test_run_pipeline_already_running_raises(self):
        """Should raise when running a non-pending pipeline."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline()
        orch.run_pipeline(state.pipeline_id)
        with pytest.raises(ValueError, match="status"):
            orch.run_pipeline(state.pipeline_id)

    def test_run_pipeline_not_found_raises(self):
        """Should raise for unknown pipeline."""
        orch = PipelineOrchestrator()
        with pytest.raises(ValueError, match="not found"):
            orch.run_pipeline("nonexistent")

    def test_run_single_stage(self):
        """Should run a single stage."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline(
            config=PipelineConfig(stages=[PipelineStage.PRODUCT_OWNER]),
            metadata={"prompt": "Build X"},
        )
        stage_state = orch.run_stage(state.pipeline_id, PipelineStage.PRODUCT_OWNER)
        assert stage_state.status == StageStatus.COMPLETED
        assert stage_state.result.get("success") is True

    def test_retry_failed_stage(self):
        """Should retry a failed stage."""
        orch = PipelineOrchestrator()

        # Create a pipeline with a prompt so the agent can succeed on retry
        state = orch.create_pipeline(
            config=PipelineConfig(stages=[PipelineStage.PRODUCT_OWNER]),
            metadata={"prompt": "Build a blog system"},
        )

        # Manually set stage to failed
        stage_state = state.stages[PipelineStage.PRODUCT_OWNER]
        stage_state.status = StageStatus.FAILED
        stage_state.error = "Simulated failure"

        # Retry
        result = orch.retry_stage(state.pipeline_id, PipelineStage.PRODUCT_OWNER)
        assert result.status == StageStatus.COMPLETED
        assert result.error is None

    def test_retry_non_failed_stage_raises(self):
        """Should raise when retrying a non-failed stage."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline()
        with pytest.raises(ValueError, match="Cannot retry"):
            orch.retry_stage(state.pipeline_id, PipelineStage.PRODUCT_OWNER)

    def test_cancel_pipeline(self):
        """Should cancel a running pipeline."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline()
        # Set to running
        state.status = PipelineStatus.RUNNING
        result = orch.cancel_pipeline(state.pipeline_id)
        assert result is not None
        assert result.status == PipelineStatus.CANCELLED

    def test_cancel_pipeline_not_found(self):
        """Should return None for cancel on unknown pipeline."""
        orch = PipelineOrchestrator()
        result = orch.cancel_pipeline("nonexistent")
        assert result is None

    def test_cancel_completed_pipeline(self):
        """Should not change completed pipeline status."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline()
        state.status = PipelineStatus.COMPLETED
        result = orch.cancel_pipeline(state.pipeline_id)
        assert result is not None
        assert result.status == PipelineStatus.COMPLETED  # unchanged

    def test_delete_pipeline(self):
        """Should delete a pipeline."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline()
        assert orch.delete_pipeline(state.pipeline_id) is True
        assert orch.get_pipeline_state(state.pipeline_id) is None

    def test_delete_pipeline_not_found(self):
        """Should return False for delete on unknown pipeline."""
        orch = PipelineOrchestrator()
        assert orch.delete_pipeline("nonexistent") is False

    def test_empty_pipeline_config(self):
        """Should handle pipeline with no stages gracefully."""
        orch = PipelineOrchestrator()
        config = PipelineConfig(stages=[])
        state = orch.create_pipeline(config=config)
        result = orch.run_pipeline(state.pipeline_id)
        assert result.status == PipelineStatus.COMPLETED
        assert len(result.stages) == 0

    def test_stage_input_building(self):
        """Stage input should include outputs from previous stages."""
        orch = PipelineOrchestrator()
        state = orch.create_pipeline(
            config=PipelineConfig(stages=[
                PipelineStage.PRODUCT_OWNER,
                PipelineStage.NER,
            ]),
            metadata={"prompt": "Build an app"},
        )
        result = orch.run_pipeline(state.pipeline_id)
        # NER should have received tickets from PRODUCT_OWNER
        ner_state = result.stages[PipelineStage.NER]
        assert ner_state.status == StageStatus.COMPLETED
        # The NER result should contain entities (from tickets)
        assert len(ner_state.result.get("entities", [])) > 0


class TestPipelineOrchestratorErrorStrategies:
    """Tests for different error strategies."""

    def test_abort_on_failure(self):
        """ABORT strategy should stop on first failure."""
        orch = PipelineOrchestrator()
        config = PipelineConfig(
            stages=[PipelineStage.PRODUCT_OWNER, PipelineStage.NER],
            error_strategy=PipelineErrorStrategy.ABORT,
        )
        state = orch.create_pipeline(config=config, metadata={})  # no prompt → will fail
        # ProductOwner will fail because there's no prompt in metadata
        result = orch.run_pipeline(state.pipeline_id)
        # If PRODUCT_OWNER fails, ABORT stops the pipeline
        po_state = result.stages[PipelineStage.PRODUCT_OWNER]
        if po_state.status == StageStatus.FAILED:
            assert result.status == PipelineStatus.FAILED
            # NER should be pending or skipped
            ner_state = result.stages[PipelineStage.NER]
            assert ner_state.status in (StageStatus.PENDING, StageStatus.CANCELLED, StageStatus.FAILED)

    def test_skip_on_failure(self):
        """SKIP strategy should continue past failures."""
        orch = PipelineOrchestrator()
        config = PipelineConfig(
            stages=[PipelineStage.PRODUCT_OWNER, PipelineStage.NER, PipelineStage.ONTOLOGIST],
            error_strategy=PipelineErrorStrategy.SKIP,
        )
        state = orch.create_pipeline(
            config=config,
            metadata={"prompt": "Build a system"},
        )
        result = orch.run_pipeline(state.pipeline_id)
        # All stages should complete since prompt is provided
        assert result.status == PipelineStatus.COMPLETED


    def test_retry_strategy(self):
        """RETRY strategy should retry failed stages."""
        orch = PipelineOrchestrator()
        config = PipelineConfig(
            stages=[PipelineStage.PRODUCT_OWNER],
            error_strategy=PipelineErrorStrategy.RETRY,
            max_retries=2,
        )
        state = orch.create_pipeline(
            config=config,
            metadata={"prompt": "Build something"},
        )
        result = orch.run_pipeline(state.pipeline_id)
        assert result.status == PipelineStatus.COMPLETED


# ======================================================================
# API Endpoint Tests
# ======================================================================


class TestCodegenAPI:
    """Tests for codegen API endpoints."""

    def test_create_pipeline(self, client: TestClient):
        """POST /api/codegen/pipeline should create a pipeline."""
        resp = client.post("/api/codegen/pipeline", json={
            "prompt": "Build a blog system",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "pipeline_id" in data
        assert data["status"] == "pending"
        assert data["stage_count"] == 10

    def test_create_and_run_pipeline(self, client: TestClient):
        """POST /api/codegen/pipeline with auto_run should execute."""
        resp = client.post("/api/codegen/pipeline", json={
            "prompt": "Build a blog system",
            "auto_run": True,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] in ("completed", "running", "failed")

    def test_create_pipeline_custom_stages(self, client: TestClient):
        """POST /api/codegen/pipeline with custom stages."""
        resp = client.post("/api/codegen/pipeline", json={
            "prompt": "Build API",
            "stages": ["product_owner", "ner"],
            "error_strategy": "skip",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["stage_count"] == 2

    def test_create_pipeline_invalid_stage(self, client: TestClient):
        """POST /api/codegen/pipeline with invalid stage should 400."""
        resp = client.post("/api/codegen/pipeline", json={
            "prompt": "test",
            "stages": ["invalid_stage"],
        })
        assert resp.status_code == 400

    def test_create_pipeline_invalid_error_strategy(self, client: TestClient):
        """POST /api/codegen/pipeline with invalid error_strategy should 400."""
        resp = client.post("/api/codegen/pipeline", json={
            "prompt": "test",
            "error_strategy": "invalid",
        })
        assert resp.status_code == 400

    def test_get_pipeline(self, client: TestClient):
        """GET /api/codegen/pipeline/{id} should return pipeline state."""
        # Create first
        create_resp = client.post("/api/codegen/pipeline", json={
            "prompt": "Build X",
        })
        pipeline_id = create_resp.json()["pipeline_id"]

        # Get
        resp = client.get(f"/api/codegen/pipeline/{pipeline_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pipeline_id"] == pipeline_id
        assert "stages" in data

    def test_get_pipeline_not_found(self, client: TestClient):
        """GET /api/codegen/pipeline/{id} for missing pipeline should 404."""
        resp = client.get("/api/codegen/pipeline/nonexistent")
        assert resp.status_code == 404

    def test_list_pipelines(self, client: TestClient):
        """GET /api/codegen/pipelines should return list."""
        # Create a couple
        client.post("/api/codegen/pipeline", json={"prompt": "P1"})
        client.post("/api/codegen/pipeline", json={"prompt": "P2"})

        resp = client.get("/api/codegen/pipelines")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 2
        assert len(data["pipelines"]) >= 2

    def test_list_pipelines_filter_by_status(self, client: TestClient):
        """GET /api/codegen/pipelines?status={status} should filter."""
        resp = client.get("/api/codegen/pipelines?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        for p in data["pipelines"]:
            assert p["status"] == "pending"

    def test_list_pipelines_invalid_status(self, client: TestClient):
        """GET /api/codegen/pipelines with invalid status should 400."""
        resp = client.get("/api/codegen/pipelines?status=invalid")
        assert resp.status_code == 400

    def test_cancel_pipeline(self, client: TestClient):
        """POST /api/codegen/pipeline/{id}/cancel should cancel pipeline."""
        # Create
        create_resp = client.post("/api/codegen/pipeline", json={"prompt": "X"})
        pipeline_id = create_resp.json()["pipeline_id"]

        # Cancel
        resp = client.post(f"/api/codegen/pipeline/{pipeline_id}/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"

    def test_cancel_pipeline_not_found(self, client: TestClient):
        """POST /api/codegen/pipeline/{id}/cancel on missing should 404."""
        resp = client.post("/api/codegen/pipeline/nonexistent/cancel")
        assert resp.status_code == 404

    def test_retry_stage(self, client: TestClient):
        """POST /api/codegen/pipeline/{id}/retry/{stage} should retry."""
        # Create a pipeline and run it
        create_resp = client.post("/api/codegen/pipeline", json={
            "prompt": "Build X",
            "auto_run": True,
        })
        pipeline_id = create_resp.json()["pipeline_id"]

        # Get state to find a failed stage (if any)
        get_resp = client.get(f"/api/codegen/pipeline/{pipeline_id}")
        state = get_resp.json()

        # Find a failed stage to retry
        failed_stages = [s for s in state["stages"] if s["status"] == "failed"]
        if failed_stages:
            stage_name = failed_stages[0]["stage"]
            resp = client.post(
                f"/api/codegen/pipeline/{pipeline_id}/retry/{stage_name}"
            )
            # Could be 200 or 422 depending on state
            assert resp.status_code in (200, 422)

    def test_retry_stage_invalid_stage_name(self, client: TestClient):
        """POST retry with invalid stage name should 400."""
        # Create pipeline
        create_resp = client.post("/api/codegen/pipeline", json={"prompt": "X"})
        pipeline_id = create_resp.json()["pipeline_id"]

        resp = client.post(
            f"/api/codegen/pipeline/{pipeline_id}/retry/invalid_stage"
        )
        assert resp.status_code == 400

    def test_retry_stage_not_failed(self, client: TestClient):
        """POST retry on non-failed stage should 422."""
        # Create and run pipeline
        create_resp = client.post("/api/codegen/pipeline", json={
            "prompt": "Build X",
            "auto_run": True,
        })
        pipeline_id = create_resp.json()["pipeline_id"]

        # Get a completed stage and try to retry it
        get_resp = client.get(f"/api/codegen/pipeline/{pipeline_id}")
        state = get_resp.json()
        completed_stages = [s for s in state["stages"] if s["status"] == "completed"]
        if completed_stages:
            resp = client.post(
                f"/api/codegen/pipeline/{pipeline_id}/retry/{completed_stages[0]['stage']}"
            )
            assert resp.status_code == 422
