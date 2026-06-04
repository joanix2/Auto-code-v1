"""
Template Controller - REST API endpoints for template and generation management.

Provides endpoints for:
- Listing and registering templates
- Rendering templates with context
- Creating and executing generation plans
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.database import get_db
from src.models.oauth.user import User
from src.services.query.query_service import QueryService
from src.services.templates import (
    ExecutionResult,
    GenerationPlan,
    GenerationStep,
    PlanExecutor,
    TemplateRegistry,
    TemplateRenderer,
    topological_sort,
    validate_plan,
)
from src.services.templates.template_renderer import TemplateRenderError
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])

# ------------------------------------------------------------------
# Global instances (singleton-like for now; could be made configurable)
# ------------------------------------------------------------------

_registry: TemplateRegistry | None = None
_renderer: TemplateRenderer | None = None


def get_registry() -> TemplateRegistry:
    """Get or create the global TemplateRegistry."""
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
    return _registry


def get_renderer(registry: TemplateRegistry = Depends(get_registry)) -> TemplateRenderer:
    """Get or create the global TemplateRenderer."""
    global _renderer
    if _renderer is None:
        _renderer = TemplateRenderer(registry)
    return _renderer


def get_query_service(db=Depends(get_db)) -> QueryService:
    """FastAPI dependency to get a QueryService instance."""
    return QueryService(db)


# ======================================================================
# Template Management Endpoints
# ======================================================================


@router.get("")
async def list_templates(
    current_user: User = Depends(get_current_user),
    registry: TemplateRegistry = Depends(get_registry),
):
    """List all registered templates.

    Returns:
        Dict with template names and optional metadata.
    """
    templates = registry.list_templates()
    result = []
    for name in templates:
        info = {
            "name": name,
            "metadata": registry.get_metadata(name),
        }
        # Check if template is associated with a kind
        for kind in ("concept", "attribute", "relation"):
            if name in registry.get_templates_by_kind(kind):
                info["kind"] = kind
                break
        result.append(info)

    return {"templates": result, "count": len(result)}


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_template(
    data: dict[str, Any],
    current_user: User = Depends(get_current_user),
    registry: TemplateRegistry = Depends(get_registry),
):
    """Register a new template.

    Request body:
        name (str): Template name (unique).
        template (str): Jinja2 template content.
        kind (str, optional): Node kind association.
        metadata (dict, optional): Template metadata.

    Returns:
        Confirmation with template name.
    """
    name = data.get("name")
    template_string = data.get("template")

    if not name or not template_string:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both 'name' and 'template' fields are required",
        )

    try:
        registry.register_template(
            name=name,
            template_string=template_string,
            kind=data.get("kind"),
            metadata=data.get("metadata"),
        )
        logger.info(f"Registered template '{name}' via API")
        return {"message": f"Template '{name}' registered", "name": name}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/{template_name}")
async def get_template_info(
    template_name: str = Path(..., description="Template name"),
    current_user: User = Depends(get_current_user),
    registry: TemplateRegistry = Depends(get_registry),
):
    """Get information about a specific template."""
    if not registry.has_template(template_name):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_name}' not found",
        )

    metadata = registry.get_metadata(template_name)
    return {
        "name": template_name,
        "metadata": metadata,
    }


@router.delete("/{template_name}")
async def delete_template(
    template_name: str = Path(..., description="Template name"),
    current_user: User = Depends(get_current_user),
    registry: TemplateRegistry = Depends(get_registry),
):
    """Delete a registered template."""
    try:
        registry.remove_template(template_name)
        return {"message": f"Template '{template_name}' removed"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# ======================================================================
# Rendering Endpoints
# ======================================================================


@router.post("/render")
async def render_template(
    data: dict[str, Any],
    current_user: User = Depends(get_current_user),
    renderer: TemplateRenderer = Depends(get_renderer),
):
    """Render a template with provided context.

    Request body:
        template_name (str): Name of the registered template.
        context (dict): Template context variables.
        template_string (str, optional): Inline template (overrides template_name).

    Returns:
        Rendered output as a string.
    """
    template_name = data.get("template_name")
    context = data.get("context", {})
    template_string = data.get("template_string")

    try:
        if template_string:
            output = renderer.render_from_string(template_string, context)
        elif template_name:
            output = renderer.render_template(template_name, context)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either 'template_name' or 'template_string'",
            )

        return {"output": output, "template_name": template_name or "<inline>"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except TemplateRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post("/render-entity/{entity_id}")
async def render_entity_template(
    entity_id: str = Path(..., description="Entity node ID"),
    data: dict[str, Any] | None = None,
    max_depth: int = Query(
        5, ge=1, le=20, description="Maximum recursion depth for entity tree"
    ),
    current_user: User = Depends(get_current_user),
    renderer: TemplateRenderer = Depends(get_renderer),
    query_service: QueryService = Depends(get_query_service),
):
    """Render a template using an entity tree as context.

    Request body (optional):
        template_name (str): Name of the registered template.
        template_string (str, optional): Inline template (overrides template_name).
        extra_context (dict, optional): Additional context variables.

    Returns:
        Rendered output and entity tree summary.
    """
    data = data or {}
    template_name = data.get("template_name")
    template_string = data.get("template_string")
    extra_context = data.get("extra_context", {})

    if not template_name and not template_string:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either 'template_name' or 'template_string'",
        )

    # Fetch entity tree
    entity_tree = query_service.get_entity_tree(
        root_id=entity_id, max_depth=max_depth
    )

    if entity_tree is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity '{entity_id}' not found",
        )

    try:
        if template_string:
            # Build context the same way render_from_entity does
            context: dict[str, Any] = {
                "entity_tree": entity_tree,
                "entity": entity_tree.get("entity", {}),
                "fields": entity_tree.get("fields", []),
                "relations": entity_tree.get("relations", []),
            }
            context.update(extra_context)
            output = renderer.render_from_string(template_string, context)
        else:
            output = renderer.render_from_entity(
                entity_tree, template_name, extra_context
            )

        return {
            "output": output,
            "template_name": template_name or "<inline>",
            "entity": {
                "id": entity_tree.get("entity", {}).get("id"),
                "name": entity_tree.get("entity", {}).get("name"),
                "kind": entity_tree.get("entity", {}).get("_kind"),
                "field_count": len(entity_tree.get("fields", [])),
                "relation_count": len(entity_tree.get("relations", [])),
            },
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except TemplateRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


# ======================================================================
# Generation Plan Endpoints
# ======================================================================


@router.post("/plan")
async def create_plan(
    data: dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    """Create and validate a generation plan.

    Request body:
        name (str): Plan name.
        steps (list): List of step objects with:
            name (str): Step name.
            template_name (str): Template to render.
            entity_id (str, optional): Entity node ID.
            depends_on (list[str], optional): Step dependencies.
            output_path (str, optional): Output file path.
            context_overrides (dict, optional): Extra context.

    Returns:
        The validated plan and a summary.
    """
    try:
        steps_data = data.get("steps", [])
        steps = [GenerationStep(**s) for s in steps_data]

        plan = GenerationPlan(
            id=data.get("id", ""),
            name=data["name"],
            steps=steps,
            execution_mode=data.get("execution_mode", "sequential"),
            error_strategy=data.get("error_strategy", "abort"),
        )

        # Validate
        errors = validate_plan(plan)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"plan": plan.model_dump(), "errors": errors},
            )

        # Compute execution order
        ordered = topological_sort(steps)

        return {
            "plan": plan.model_dump(),
            "execution_order": [s.name for s in ordered],
            "step_count": len(steps),
            "valid": True,
        }

    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required field: {e}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.post("/execute")
async def execute_plan(
    data: dict[str, Any],
    current_user: User = Depends(get_current_user),
    renderer: TemplateRenderer = Depends(get_renderer),
    query_service: QueryService = Depends(get_query_service),
):
    """Execute a generation plan.

    Request body:
        plan (dict): The generation plan (same format as POST /plan).
            name (str): Plan name.
            steps (list): List of step objects.
            execution_mode (str, optional): 'sequential' or 'parallel'.
            error_strategy (str, optional): 'abort', 'skip', or 'retry'.

    Returns:
        Plan execution results with per-step outcomes.
    """
    try:
        steps_data = data.get("plan", data).get("steps", data.get("steps", []))
        steps = [GenerationStep(**s) for s in steps_data]

        plan_data = data.get("plan", data)
        plan = GenerationPlan(
            id=plan_data.get("id", ""),
            name=plan_data.get("name", "adhoc-plan"),
            steps=steps,
            execution_mode=plan_data.get("execution_mode", "sequential"),
            error_strategy=plan_data.get("error_strategy", "abort"),
            retry_policy=plan_data.get("retry_policy", {"max_retries": 3}),
        )

        executor = PlanExecutor(renderer=renderer, query_service=query_service)
        result = executor.execute_plan(plan, query_service=query_service)

        return {
            "plan_name": result.plan_name,
            "success": result.success,
            "total_duration_ms": result.total_duration_ms,
            "step_count": len(result.step_results),
            "successful_count": len(result.successful_steps),
            "failed_count": len(result.failed_steps),
            "steps": [
                {
                    "step_name": r.step_name,
                    "success": r.success,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                }
                for r in result.step_results
            ],
            "output_files": result.output_files,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Plan execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan execution failed: {e}",
        )
