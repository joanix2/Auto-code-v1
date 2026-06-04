"""
Generation Plan - Models and algorithms for defining code generation workflows.

A GenerationPlan consists of ordered GenerationSteps that describe what templates
to render and how to assemble the outputs into files.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Execution mode for a generation step."""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class ErrorStrategy(str, Enum):
    """Error handling strategy for plan execution."""

    ABORT = "abort"          # Stop execution on first error
    SKIP = "skip"            # Skip failed steps, continue with others
    RETRY = "retry"          # Retry failed steps


class RetryPolicy(BaseModel):
    """Configuration for retry behavior when ErrorStrategy is RETRY."""

    max_retries: int = Field(default=3, ge=0, description="Maximum number of retry attempts")
    delay_seconds: float = Field(default=1.0, ge=0, description="Delay between retries in seconds")
    backoff_multiplier: float = Field(
        default=2.0, ge=1.0, description="Multiplier for delay after each retry"
    )


class GenerationStep(BaseModel):
    """A single step in a generation plan.

    Each step specifies:
    - Which template to render
    - Which entity (by ID) provides the data
    - Any dependencies on other steps
    - Where to write the output
    """

    name: str = Field(..., description="Unique name for this step within the plan")
    template_name: str = Field(..., description="Name of the registered template to render")
    entity_id: str | None = Field(
        default=None,
        description="ID of the entity (node) used as context for rendering",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="Names of steps that must complete before this one",
    )
    output_path: str | None = Field(
        default=None,
        description="Relative path for the output file (optional)",
    )
    context_overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context variables merged into the template context",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for this step (e.g., tags, notes)",
    )

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Step name must not be empty")
        return v.strip()

    @field_validator("depends_on")
    @classmethod
    def depends_on_must_not_self_reference(cls, v: list[str], info: Any) -> list[str]:
        if info.data.get("name") and info.data["name"] in v:
            raise ValueError(f"Step '{info.data['name']}' cannot depend on itself")
        return v


class GenerationPlan(BaseModel):
    """A complete generation plan.

    Defines a series of steps to render templates, optionally in dependency order,
    producing output files from graph entities.
    """

    id: str = Field(default="", description="Unique identifier for the plan")
    name: str = Field(..., description="Human-readable name for the plan")
    steps: list[GenerationStep] = Field(
        default_factory=list, description="Ordered list of generation steps"
    )
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.SEQUENTIAL,
        description="Default execution mode for independent steps",
    )
    error_strategy: ErrorStrategy = Field(
        default=ErrorStrategy.ABORT,
        description="Error handling strategy during execution",
    )
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Retry policy (used when error_strategy is RETRY)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata for the plan",
    )


# ------------------------------------------------------------------
# Algorithms
# ------------------------------------------------------------------


def topological_sort(steps: list[GenerationStep]) -> list[GenerationStep]:
    """Topological sort of generation steps respecting dependencies.

    Uses Kahn's algorithm. Steps with no dependencies come first,
    then steps whose dependencies have been satisfied.

    Args:
        steps: List of GenerationStep instances.

    Returns:
        List of steps in topological order.

    Raises:
        ValueError: If the dependency graph contains a cycle.
    """
    # Build adjacency and in-degree maps
    step_map = {s.name: s for s in steps}
    in_degree: dict[str, int] = {s.name: 0 for s in steps}
    adjacency: dict[str, list[str]] = {s.name: [] for s in steps}

    for step in steps:
        for dep in step.depends_on:
            if dep not in step_map:
                raise ValueError(
                    f"Step '{step.name}' depends on unknown step '{dep}'"
                )
            adjacency[dep].append(step.name)
            in_degree[step.name] = in_degree.get(step.name, 0) + 1

    # Kahn's algorithm
    queue = [name for name, degree in in_degree.items() if degree == 0]
    sorted_names: list[str] = []

    while queue:
        # Sort to ensure deterministic output
        queue.sort()
        current = queue.pop(0)
        sorted_names.append(current)

        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_names) != len(steps):
        cycle_nodes = [s for s in steps if s.name not in sorted_names]
        raise ValueError(
            f"Circular dependency detected among steps: "
            f"{', '.join(s.name for s in cycle_nodes)}"
        )

    # Return steps in sorted order, preserving original objects
    name_order = {name: idx for idx, name in enumerate(sorted_names)}
    sorted_steps = sorted(steps, key=lambda s: name_order[s.name])
    return sorted_steps


def validate_plan(plan: GenerationPlan) -> list[str]:
    """Validate a generation plan.

    Checks:
    - All steps have unique names
    - All dependency references are valid
    - No circular dependencies
    - At least one step exists

    Args:
        plan: The GenerationPlan to validate.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []

    if not plan.steps:
        errors.append("Plan must have at least one step")
        return errors

    # Check for duplicate step names
    names = [s.name for s in plan.steps]
    duplicates = set(n for n in names if names.count(n) > 1)
    if duplicates:
        errors.append(f"Duplicate step names: {', '.join(sorted(duplicates))}")

    # Build set of known step names
    known_names = set(names)

    # Check dependency references
    for step in plan.steps:
        for dep in step.depends_on:
            if dep not in known_names:
                errors.append(
                    f"Step '{step.name}' depends on unknown step '{dep}'"
                )
            if dep == step.name:
                errors.append(f"Step '{step.name}' depends on itself")

    # Check for cycles using topological_sort
    if not errors:
        try:
            topological_sort(plan.steps)
        except ValueError as e:
            errors.append(str(e))

    return errors
