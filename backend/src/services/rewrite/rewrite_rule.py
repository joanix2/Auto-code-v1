"""Rewrite Rule — a named, versioned transformation (condition + action).

A :class:`RewriteRule` pairs a *condition* (a predicate that decides whether
the rule applies) with an *action* (a pure function that transforms the graph).

Callables are stored by reference for engine execution; metadata fields
(name, description, priority, enabled) support display, ordering, and
filtering in the API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# Condition: receives the full graph dict, returns True if the rule applies.
ConditionFn = Callable[[dict[str, Any]], bool]

# Action: receives the full graph dict, returns a *new* modified graph dict.
ActionFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class RewriteRule:
    """A single rewrite rule.

    Attributes:
        name:        Unique, human-readable identifier (e.g. ``"normalize_names"``).
        description: Explanation of what this rule does and why.
        condition:   Predicate called with the graph dict. Return ``True`` to fire.
        action:      Pure transformation: receives graph dict, returns a new one.
        priority:    Lower numbers run first (default 100).
        enabled:     When ``False`` the rule is skipped by the engine.
        version:     Optional semantic version string for the rule.
    """

    name: str
    description: str
    condition: ConditionFn
    action: ActionFn
    priority: int = 100
    enabled: bool = True
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata (callables cannot be JSON-serialised)."""
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
            "version": self.version,
        }

    def __call__(self, graph: dict[str, Any]) -> dict[str, Any] | None:
        """Evaluate *condition*; if true, return *action*(graph), else ``None``."""
        if not self.enabled:
            return None
        if not self.condition(graph):
            return None
        return self.action(graph)
