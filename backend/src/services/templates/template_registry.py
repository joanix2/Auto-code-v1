"""
Template Registry - Manages registration, listing, and loading of Jinja2 templates.

Templates can be registered from strings or loaded from a directory of .j2 files.
Each template can optionally be associated with a node kind (concept, attribute, relation)
to support kind-based template resolution.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import BaseLoader, Environment, StrictUndefined, Template, TemplateNotFound

logger = logging.getLogger(__name__)


class TemplateRegistry:
    """Registry for Jinja2 templates.

    Provides methods to register, list, and load templates.
    Templates can be associated with a node kind for kind-based resolution.

    Attributes:
        _templates: Dict mapping template name to Jinja2 Template object.
        _kind_mapping: Dict mapping node kind to list of template names.
        _metadata: Dict mapping template name to optional metadata dict.
    """

    def __init__(self, env: Environment | None = None) -> None:
        self._templates: dict[str, Template] = {}
        self._kind_mapping: dict[str, list[str]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._env = env or Environment(autoescape=False)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_template(
        self,
        name: str,
        template_string: str,
        kind: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a template from a string.

        Args:
            name: Unique name for the template (e.g., 'python_model').
            template_string: The Jinja2 template content.
            kind: Optional node kind this template is associated with
                  ('concept', 'attribute', 'relation', or None for generic).
            metadata: Optional dict of metadata for the template.

        Raises:
            ValueError: If a template with the same name is already registered.
        """
        if name in self._templates:
            raise ValueError(f"Template '{name}' is already registered")

        template = self._env.from_string(template_string)
        self._templates[name] = template
        self._metadata[name] = metadata or {}

        if kind:
            if kind not in self._kind_mapping:
                self._kind_mapping[kind] = []
            self._kind_mapping[kind].append(name)

        logger.debug(f"Registered template '{name}' (kind={kind})")

    def register_template_from_file(self, file_path: str | Path) -> str:
        """Register a template from a .j2 file on disk.

        The template name is derived from the filename (without .j2 extension).

        Args:
            file_path: Path to the .j2 template file.

        Returns:
            The registered template name.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a .j2 file.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {path}")
        if path.suffix not in (".j2", ".jinja2"):
            raise ValueError(f"Template file must have .j2 extension: {path}")

        name = path.stem  # filename without .j2
        template_string = path.read_text(encoding="utf-8")
        self.register_template(name, template_string)
        return name

    # ------------------------------------------------------------------
    # Bulk loading
    # ------------------------------------------------------------------

    def load_from_directory(
        self,
        directory_path: str | Path,
        kind_mapping: dict[str, str] | None = None,
    ) -> list[str]:
        """Load all .j2 template files from a directory.

        Each file becomes a template named after its filename (without .j2).
        A kind_mapping can map template names to node kinds.

        Args:
            directory_path: Path to directory containing .j2 files.
            kind_mapping: Optional dict mapping template name → node kind.

        Returns:
            List of registered template names.

        Raises:
            FileNotFoundError: If the directory does not exist.
        """
        path = Path(directory_path)
        if not path.is_dir():
            raise FileNotFoundError(f"Template directory not found: {path}")

        kind_mapping = kind_mapping or {}
        registered: list[str] = []

        for file_path in sorted(path.iterdir()):
            if file_path.suffix not in (".j2", ".jinja2"):
                continue

            name = file_path.stem
            kind = kind_mapping.get(name)
            template_string = file_path.read_text(encoding="utf-8")
            self.register_template(name, template_string, kind=kind)
            registered.append(name)
            logger.info(f"Loaded template '{name}' from {file_path}")

        return registered

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def list_templates(self) -> list[str]:
        """Return sorted list of all registered template names.

        Returns:
            Sorted list of template name strings.
        """
        return sorted(self._templates.keys())

    def get_template(self, name: str) -> Template:
        """Get a registered template by name.

        Args:
            name: Template name.

        Returns:
            The Jinja2 Template object.

        Raises:
            ValueError: If the template is not found.
        """
        template = self._templates.get(name)
        if template is None:
            raise ValueError(
                f"Template '{name}' not found. "
                f"Registered templates: {', '.join(self.list_templates())}"
            )
        return template

    def get_templates_by_kind(self, kind: str) -> list[str]:
        """Get all template names associated with a given node kind.

        Args:
            kind: Node kind ('concept', 'attribute', 'relation').

        Returns:
            List of template names for this kind.
        """
        return self._kind_mapping.get(kind, [])

    def get_metadata(self, name: str) -> dict[str, Any]:
        """Get metadata for a registered template.

        Args:
            name: Template name.

        Returns:
            Metadata dict (empty if none was provided).

        Raises:
            ValueError: If the template is not found.
        """
        if name not in self._metadata:
            raise ValueError(f"Template '{name}' not found")
        return self._metadata[name]

    def has_template(self, name: str) -> bool:
        """Check if a template is registered.

        Args:
            name: Template name.

        Returns:
            True if the template exists, False otherwise.
        """
        return name in self._templates

    def remove_template(self, name: str) -> None:
        """Remove a registered template.

        Args:
            name: Template name.

        Raises:
            ValueError: If the template is not found.
        """
        if name not in self._templates:
            raise ValueError(f"Template '{name}' not found")

        # Remove from kind mapping
        for kind, templates in list(self._kind_mapping.items()):
            if name in templates:
                templates.remove(name)
                if not templates:
                    del self._kind_mapping[kind]

        del self._templates[name]
        self._metadata.pop(name, None)
        logger.debug(f"Removed template '{name}'")

    def clear(self) -> None:
        """Remove all registered templates."""
        self._templates.clear()
        self._kind_mapping.clear()
        self._metadata.clear()
        logger.debug("Cleared all templates")
