"""
Template Services - Template Registry, Renderer, Generation Plan, and Executor

Provides the template system that transforms graph data into concrete files
(code, SQL, documentation, etc.) using Jinja2 templates.
"""

from .generation_plan import GenerationPlan, GenerationStep, topological_sort, validate_plan
from .plan_executor import PlanExecutor, StepResult, ExecutionResult
from .template_registry import TemplateRegistry
from .template_renderer import TemplateRenderer

__all__ = [
    "TemplateRegistry",
    "TemplateRenderer",
    "GenerationPlan",
    "GenerationStep",
    "PlanExecutor",
    "StepResult",
    "ExecutionResult",
    "topological_sort",
    "validate_plan",
]
