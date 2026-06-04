"""
Plan Executor - Executes generation plans against a QueryService.

Supports sequential and parallel step execution with hooks for
before_step, after_step, and on_error callbacks.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from src.services.query.query_service import QueryService

from .generation_plan import (
    ErrorStrategy,
    ExecutionMode,
    GenerationPlan,
    GenerationStep,
    RetryPolicy,
    topological_sort,
)
from .template_renderer import TemplateRenderError, TemplateRenderer

logger = logging.getLogger(__name__)

# Type aliases for hook callbacks
StepHook = Callable[[GenerationStep, dict[str, Any]], None]
ErrorHook = Callable[[GenerationStep, Exception], None]


class StepResult:
    """Result of executing a single generation step."""

    def __init__(
        self,
        step_name: str,
        success: bool,
        output: str | None = None,
        error: str | None = None,
        duration_ms: float = 0.0,
    ) -> None:
        self.step_name = step_name
        self.success = success
        self.output = output
        self.error = error
        self.duration_ms = duration_ms

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        return f"<StepResult {self.step_name} {status} ({self.duration_ms:.1f}ms)>"


class ExecutionResult:
    """Result of executing an entire generation plan."""

    def __init__(
        self,
        plan_name: str,
        success: bool,
        step_results: list[StepResult],
        total_duration_ms: float = 0.0,
        output_files: list[str] | None = None,
    ) -> None:
        self.plan_name = plan_name
        self.success = success
        self.step_results = step_results
        self.total_duration_ms = total_duration_ms
        self.output_files = output_files or []

    @property
    def failed_steps(self) -> list[StepResult]:
        """Get results for failed steps only."""
        return [r for r in self.step_results if not r.success]

    @property
    def successful_steps(self) -> list[StepResult]:
        """Get results for successful steps only."""
        return [r for r in self.step_results if r.success]

    def __repr__(self) -> str:
        status = "✓" if self.success else "✗"
        total = len(self.step_results)
        ok = len(self.successful_steps)
        return (
            f"<ExecutionResult {self.plan_name} {status} "
            f"({ok}/{total} steps, {self.total_duration_ms:.1f}ms)>"
        )


class PlanExecutor:
    """Executes generation plans.

    Orchestrates template rendering against graph entities through the
    QueryService, with full lifecycle hooks and error handling.

    Attributes:
        renderer: TemplateRenderer instance.
        query_service: QueryService instance for fetching entity trees.
    """

    def __init__(
        self,
        renderer: TemplateRenderer | None = None,
        query_service: QueryService | None = None,
    ) -> None:
        self.renderer = renderer or TemplateRenderer()
        self.query_service = query_service

        # Hooks
        self.before_step: StepHook | None = None
        self.after_step: StepHook | None = None
        self.on_error: ErrorHook | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute_plan(
        self,
        plan: GenerationPlan,
        query_service: QueryService | None = None,
    ) -> ExecutionResult:
        """Execute a generation plan.

        Args:
            plan: The GenerationPlan to execute.
            query_service: Optional QueryService (overrides instance attribute).

        Returns:
            ExecutionResult with per-step results.

        Raises:
            ValueError: If plan validation fails or no QueryService is available.
        """
        qs = query_service or self.query_service
        if qs is None:
            raise ValueError(
                "No QueryService provided. Pass one to execute_plan() or "
                "set PlanExecutor.query_service."
            )

        # Validate plan
        from .generation_plan import validate_plan

        errors = validate_plan(plan)
        if errors:
            raise ValueError(f"Plan validation failed: {'; '.join(errors)}")

        # Sort steps topologically
        try:
            sorted_steps = topological_sort(plan.steps)
        except ValueError as e:
            raise ValueError(f"Cannot execute plan: {e}") from e

        start_time = time.monotonic()
        step_results: list[StepResult] = []
        output_files: list[str] = []
        abort = False

        if plan.execution_mode == ExecutionMode.PARALLEL:
            step_results = self._execute_parallel(
                sorted_steps, plan, qs, output_files
            )
            abort = any(not r.success for r in step_results)
        else:
            for step in sorted_steps:
                if abort:
                    # Skip remaining steps if ABORT strategy
                    step_results.append(
                        StepResult(
                            step_name=step.name,
                            success=False,
                            error="Skipped due to previous failure",
                        )
                    )
                    continue

                result = self._execute_step(step, plan, qs, output_files)
                step_results.append(result)

                if not result.success:
                    if plan.error_strategy == ErrorStrategy.ABORT:
                        abort = True
                    elif (
                        plan.error_strategy == ErrorStrategy.RETRY
                        and result.error
                    ):
                        # Retry logic is handled inside _execute_step
                        pass

        total_duration = (time.monotonic() - start_time) * 1000.0
        all_success = all(r.success for r in step_results)

        return ExecutionResult(
            plan_name=plan.name,
            success=all_success,
            step_results=step_results,
            total_duration_ms=total_duration,
            output_files=output_files,
        )

    # ------------------------------------------------------------------
    # Internal: step execution
    # ------------------------------------------------------------------

    def _execute_step(
        self,
        step: GenerationStep,
        plan: GenerationPlan,
        query_service: QueryService,
        output_files: list[str],
    ) -> StepResult:
        """Execute a single generation step with retry logic."""
        step_start = time.monotonic()

        try:
            # Before-step hook
            if self.before_step:
                self.before_step(step, {"plan": plan})

            # Determine max retries
            max_retries = 0
            if plan.error_strategy == ErrorStrategy.RETRY:
                max_retries = plan.retry_policy.max_retries

            last_error: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        delay = plan.retry_policy.delay_seconds * (
                            plan.retry_policy.backoff_multiplier ** (attempt - 1)
                        )
                        logger.info(
                            f"Retrying step '{step.name}' "
                            f"(attempt {attempt + 1}/{max_retries + 1}) "
                            f"after {delay:.1f}s"
                        )
                        time.sleep(delay)

                    output = self._render_step(step, query_service)
                    duration = (time.monotonic() - step_start) * 1000.0

                    result = StepResult(
                        step_name=step.name,
                        success=True,
                        output=output,
                        duration_ms=duration,
                    )

                    if step.output_path:
                        output_files.append(step.output_path)

                    # After-step hook
                    if self.after_step:
                        self.after_step(step, {"plan": plan, "result": result})

                    return result

                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        continue
                    # Exhausted retries
                    raise last_error from e

        except Exception as e:
            duration = (time.monotonic() - step_start) * 1000.0

            # Error hook
            if self.on_error:
                self.on_error(step, e)

            error_msg = self._format_error(e)
            logger.error(f"Step '{step.name}' failed: {error_msg}")

            return StepResult(
                step_name=step.name,
                success=False,
                error=error_msg,
                duration_ms=duration,
            )

    def _render_step(
        self,
        step: GenerationStep,
        query_service: QueryService,
    ) -> str:
        """Render a step's template with its entity context."""
        # Build context
        context: dict[str, Any] = {
            "step": step.model_dump(),
            "step_name": step.name,
            "template_name": step.template_name,
        }

        # If entity_id is provided, fetch entity tree
        if step.entity_id:
            entity_tree = query_service.get_entity_tree(step.entity_id)
            if entity_tree is None:
                raise ValueError(
                    f"Entity '{step.entity_id}' not found for step '{step.name}'"
                )
            context["entity_tree"] = entity_tree
            context["entity"] = entity_tree.get("entity", {})
            context["fields"] = entity_tree.get("fields", [])
            context["relations"] = entity_tree.get("relations", [])

        # Merge context overrides
        context.update(step.context_overrides)

        # Render via registry
        output = self.renderer.render_template(step.template_name, context)

        # If output_path is set, write the output file
        if step.output_path:
            path = step.output_path
            if isinstance(path, str):
                import os
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(output)
                logger.info(f"Written output to {path}")

        return output

    # ------------------------------------------------------------------
    # Internal: parallel execution
    # ------------------------------------------------------------------

    def _execute_parallel(
        self,
        sorted_steps: list[GenerationStep],
        plan: GenerationPlan,
        query_service: QueryService,
        output_files: list[str],
    ) -> list[StepResult]:
        """Execute steps in parallel respecting dependency levels."""
        # Group steps by dependency level
        levels = self._compute_levels(sorted_steps)
        all_results: dict[str, StepResult] = {}
        final_results: list[StepResult] = []

        for level_steps in levels:
            with ThreadPoolExecutor(max_workers=len(level_steps)) as executor:
                future_to_step = {}
                for step in level_steps:
                    future = executor.submit(
                        self._execute_step, step, plan, query_service, output_files
                    )
                    future_to_step[future] = step

                for future in as_completed(future_to_step):
                    step = future_to_step[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        result = StepResult(
                            step_name=step.name,
                            success=False,
                            error=str(e),
                        )
                    all_results[step.name] = result
                    final_results.append(result)

        return final_results

    @staticmethod
    def _compute_levels(
        steps: list[GenerationStep],
    ) -> list[list[GenerationStep]]:
        """Group steps by dependency level for parallel execution.

        Level 0: no dependencies
        Level N: depends only on steps in levels < N
        """
        step_map = {s.name: s for s in steps}
        levels: list[list[GenerationStep]] = []
        assigned: set[str] = set()

        remaining = set(s.name for s in steps)

        while remaining:
            current_level: list[GenerationStep] = []
            for name in list(remaining):
                step = step_map[name]
                if all(dep in assigned for dep in step.depends_on):
                    current_level.append(step)

            if not current_level:
                # Should not happen if topological_sort passed
                raise ValueError(
                    f"Cannot compute levels for remaining steps: {remaining}"
                )

            levels.append(current_level)
            for step in current_level:
                assigned.add(step.name)
                remaining.remove(step.name)

        return levels

    @staticmethod
    def _format_error(error: Exception) -> str:
        """Format an exception for inclusion in StepResult."""
        if isinstance(error, TemplateRenderError):
            return str(error)
        if isinstance(error, ValueError):
            return str(error)
        return f"{type(error).__name__}: {error}"
