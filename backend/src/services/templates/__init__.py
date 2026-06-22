"""
Template Services — Template Registry and Renderer.

Provides the template system that transforms graph data into concrete files
(code, SQL, documentation, etc.) using Jinja2 templates.
"""

from .template_registry import TemplateRegistry
from .template_renderer import TemplateRenderer

__all__ = [
    "TemplateRegistry",
    "TemplateRenderer",
]
