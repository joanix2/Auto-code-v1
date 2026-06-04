"""
Template Renderer - Jinja2 rendering with custom filters and enriched context.

Provides rendering services with custom Jinja2 filters (snake_case, camelCase,
PascalCase, pluralize, capitalize_first) and helpers to render entity trees
returned by the QueryService.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from jinja2 import (
    BaseLoader,
    Environment,
    StrictUndefined,
    Template,
    TemplateNotFound,
    UndefinedError,
)

from .template_registry import TemplateRegistry

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Custom Jinja2 Filters
# ------------------------------------------------------------------


def filter_snake_case(value: str) -> str:
    """Convert a string to snake_case.

    Handles CamelCase, PascalCase, space-separated, and hyphenated input.

    Examples:
        'MyClass' → 'my_class'
        'firstName' → 'first_name'
        'user-id' → 'user_id'
        '  spaced  name ' → 'spaced_name'
    """
    if not isinstance(value, str):
        return str(value)
    # Insert underscores before uppercase letters (camelCase → snake_case)
    s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    # Handle consecutive uppercase (HTTPResponse → http_response)
    s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s1)
    # Replace spaces/hyphens with underscores
    s3 = re.sub(r"[\s\-]+", "_", s2)
    # Remove any remaining non-alphanumeric chars except underscores
    s4 = re.sub(r"[^\w]", "", s3)
    return s4.strip("_").lower()


def filter_camel_case(value: str) -> str:
    """Convert a string to camelCase.

    Examples:
        'my_class' → 'myClass'
        'MyClass' → 'myClass'
        'user-id' → 'userId'
    """
    if not isinstance(value, str):
        return str(value)
    # First convert to snake_case for normalization
    snake = filter_snake_case(value)
    # Split by underscore and capitalize each segment except the first
    parts = snake.split("_")
    if len(parts) <= 1:
        return parts[0]
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def filter_pascal_case(value: str) -> str:
    """Convert a string to PascalCase.

    Examples:
        'my_class' → 'MyClass'
        'firstName' → 'FirstName'
        'user-id' → 'UserId'
    """
    if not isinstance(value, str):
        return str(value)
    snake = filter_snake_case(value)
    return "".join(p.capitalize() for p in snake.split("_"))


def filter_pluralize(value: str) -> str:
    """Simple English pluralization.

    Handles common cases: -y → -ies, -s/-sh/-ch/-x → -es, etc.
    Falls back to appending 's'.

    Examples:
        'category' → 'categories'
        'class' → 'classes'
        'box' → 'boxes'
        'user' → 'users'
    """
    if not isinstance(value, str) or not value:
        return value

    # Rules for irregular/common plurals
    irregulars = {
        "person": "people",
        "child": "children",
        "foot": "feet",
        "tooth": "teeth",
        "mouse": "mice",
        "sheep": "sheep",
        "deer": "deer",
        "fish": "fish",
        "ox": "oxen",
        "goose": "geese",
    }

    lower_val = value.lower()
    if lower_val in irregulars:
        # Preserve original casing pattern
        if value[0].isupper():
            return irregulars[lower_val].capitalize()
        return irregulars[lower_val]

    # Words ending in -y preceded by consonant → -ies
    if value.endswith("y") and len(value) > 1 and value[-2].lower() not in "aeiou":
        return value[:-1] + "ies"

    # Words ending in -s, -sh, -ch, -x, -z → -es
    if value.endswith(("s", "sh", "ch", "x", "z")):
        return value + "es"

    # Words ending in -f or -fe → -ves
    if value.endswith("fe"):
        return value[:-2] + "ves"
    if value.endswith("f") and not value.endswith("ff"):
        return value[:-1] + "ves"

    # Default: add 's'
    return value + "s"


def filter_capitalize_first(value: str) -> str:
    """Capitalize the first character of a string.

    Args:
        value: Input string.

    Returns:
        String with first character capitalized, rest unchanged.
    """
    if not isinstance(value, str) or not value:
        return value
    return value[0].upper() + value[1:] if len(value) > 1 else value[0].upper()


# ------------------------------------------------------------------
# Error types
# ------------------------------------------------------------------


class TemplateRenderError(Exception):
    """Raised when template rendering fails with context about the error."""

    def __init__(
        self,
        template_name: str,
        message: str,
        line: int | None = None,
        cause: str | None = None,
    ) -> None:
        self.template_name = template_name
        self.line = line
        self.cause = cause
        detail = f"Template '{template_name}'"
        if line is not None:
            detail += f" at line {line}"
        detail += f": {message}"
        if cause:
            detail += f" (cause: {cause})"
        super().__init__(detail)


# ------------------------------------------------------------------
# Renderer
# ------------------------------------------------------------------

_FILTERS: dict[str, Any] = {
    "snake_case": filter_snake_case,
    "camel_case": filter_camel_case,
    "PascalCase": filter_pascal_case,
    "pluralize": filter_pluralize,
    "capitalize_first": filter_capitalize_first,
}


class TemplateRenderer:
    """Renders Jinja2 templates with custom filters and enriched context.

    The renderer uses a TemplateRegistry to resolve templates and provides
    a Jinja2 Environment with custom filters pre-configured.

    Attributes:
        registry: The TemplateRegistry instance to resolve template names.
        env: The Jinja2 Environment with custom filters.
    """

    def __init__(self, registry: TemplateRegistry | None = None) -> None:
        # Build a Jinja2 Environment with custom filters
        # StrictUndefined ensures missing variables raise errors
        self.env = Environment(autoescape=False, undefined=StrictUndefined)
        for name, func in _FILTERS.items():
            self.env.filters[name] = func

        # Pass env to the registry so it can compile templates with filters
        if registry is not None:
            registry._env = self.env
        self.registry = registry or TemplateRegistry(env=self.env)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_template(
        self,
        template_name: str,
        context: dict[str, Any],
    ) -> str:
        """Render a registered template with the given context.

        The context is enriched with utility functions before rendering.

        Args:
            template_name: Name of the registered template.
            context: Dict of variables to pass to the template.

        Returns:
            Rendered string output.

        Raises:
            ValueError: If the template is not registered.
            TemplateRenderError: If rendering fails due to syntax or missing variables.
        """
        template = self.registry.get_template(template_name)

        # Enrich context with utility functions
        enriched_context = dict(context)
        enriched_context.setdefault("_filters", _FILTERS)
        enriched_context.setdefault("_registry", self.registry)

        try:
            rendered = template.render(enriched_context)
            return rendered
        except UndefinedError as e:
            raise TemplateRenderError(
                template_name=template_name,
                message=f"Missing variable in template context: {e}",
                cause=str(e),
            ) from e
        except Exception as e:
            # Try to extract line number from Jinja2 error
            line = None
            if hasattr(e, "lineno"):
                line = e.lineno  # type: ignore[attr-defined]
            raise TemplateRenderError(
                template_name=template_name,
                message=f"Rendering error: {e}",
                line=line,
                cause=str(e),
            ) from e

    def render_from_string(
        self,
        template_string: str,
        context: dict[str, Any],
    ) -> str:
        """Render a template string directly (without registering it).

        Useful for quick testing or one-off rendering.

        Args:
            template_string: Jinja2 template content.
            context: Dict of variables to pass to the template.

        Returns:
            Rendered string output.

        Raises:
            TemplateRenderError: If rendering fails.
        """
        try:
            template = self.env.from_string(template_string)
            rendered = template.render(context)
            return rendered
        except UndefinedError as e:
            raise TemplateRenderError(
                template_name="<inline>",
                message=f"Missing variable: {e}",
                cause=str(e),
            ) from e
        except Exception as e:
            raise TemplateRenderError(
                template_name="<inline>",
                message=f"Rendering error: {e}",
                cause=str(e),
            ) from e

    def render_from_entity(
        self,
        entity_tree: dict[str, Any],
        template_name: str,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Render a template using an entity tree as context.

        The entity tree (as returned by QueryService.get_entity_tree) is
        placed into the context as the 'entity_tree' variable, with the
        entity itself available at the top level for convenience.

        Args:
            entity_tree: The recursive entity tree dict from QueryService.
            template_name: Name of the registered template.
            extra_context: Optional additional context variables.

        Returns:
            Rendered string output.

        Raises:
            ValueError: If the template is not registered.
            TemplateRenderError: If rendering fails.
        """
        context: dict[str, Any] = {
            "entity_tree": entity_tree,
            "entity": entity_tree.get("entity", {}),
            "fields": entity_tree.get("fields", []),
            "relations": entity_tree.get("relations", []),
        }
        if extra_context:
            context.update(extra_context)

        return self.render_template(template_name, context)

    # ------------------------------------------------------------------
    # Convenience access to registry
    # ------------------------------------------------------------------

    @property
    def registry(self) -> TemplateRegistry:
        """The underlying TemplateRegistry."""
        return self._registry

    @registry.setter
    def registry(self, value: TemplateRegistry) -> None:
        self._registry = value
