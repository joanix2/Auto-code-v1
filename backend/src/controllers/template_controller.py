"""Template Controller — REST API for template management and rendering."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path

from src.services.templates import TemplateRegistry, TemplateRenderer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])

_registry: TemplateRegistry | None = None
_renderer: TemplateRenderer | None = None


def get_registry() -> TemplateRegistry:
    global _registry
    if _registry is None:
        _registry = TemplateRegistry()
        _registry.load_from_directory("templates")
    return _registry


def get_renderer() -> TemplateRenderer:
    global _renderer
    if _renderer is None:
        _renderer = TemplateRenderer(get_registry())
    return _renderer


@router.get("")
async def list_templates():
    return get_registry().list_templates()


@router.post("/register")
async def register_template(data: dict[str, Any]):
    name = data.get("name")
    content = data.get("content")
    if not name or not content:
        raise HTTPException(status_code=400, detail="'name' and 'content' are required")
    get_registry().register_template(name, content)
    return {"status": "ok", "name": name}


@router.post("/render")
async def render_template(data: dict[str, Any], renderer: TemplateRenderer = Depends(get_renderer)):
    template_name = data.get("template_name")
    template_string = data.get("template_string")
    extra_context = data.get("extra_context", {})
    if not template_name and not template_string:
        raise HTTPException(status_code=400, detail="Provide 'template_name' or 'template_string'")
    try:
        if template_string:
            output = renderer.render_from_string(template_string, extra_context)
        else:
            output = renderer.render_template(template_name, extra_context)
        return {"output": output}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{template_name}")
async def get_template(template_name: str = Path(..., description="Template name")):
    content = get_registry().get_template(template_name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    return {"name": template_name, "content": content}


@router.delete("/{template_name}")
async def delete_template(template_name: str = Path(..., description="Template name")):
    get_registry().remove_template(template_name)
    return {"status": "ok", "name": template_name}
