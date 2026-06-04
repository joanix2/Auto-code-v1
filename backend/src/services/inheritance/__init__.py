"""Inheritance Service — graph inheritance and composition.

Provides:
- ``InheritanceConfig``, ``InheritanceTree``, ``InheritedElement`` models
- ``InheritanceService`` with single and multiple inheritance resolution
- Element origin tracing across the inheritance chain
"""

from __future__ import annotations

from src.services.inheritance.inheritance_models import (
    InheritanceConfig,
    InheritanceTree,
    InheritanceType,
    InheritedElement,
)
from src.services.inheritance.inheritance_service import InheritanceService

__all__ = [
    "InheritanceConfig",
    "InheritanceTree",
    "InheritanceType",
    "InheritedElement",
    "InheritanceService",
]
