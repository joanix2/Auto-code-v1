"""Rewrite Engine — applies rewrite rules to IR graph documents.

The engine supports three modes:
1. **Single** — apply one named rule once.
2. **All** — apply every enabled rule once (in priority order).
3. **Fixpoint** — repeatedly apply rules until no rule changes the graph
   (or *max_iterations* is reached).
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from src.services.rewrite.rewrite_rule import RewriteRule

logger = logging.getLogger(__name__)


class RewriteResult:
    """Result of applying one or more rewrite rules.

    Attributes:
        success:         ``True`` when no errors occurred.
        modified_graph:  The graph dict after transformation(s).
        applied_rules:   Names of rules that were successfully applied.
        iteration_count: Number of engine iterations (fixpoint mode).
        errors:          List of error messages if any.
    """

    def __init__(
        self,
        success: bool = True,
        modified_graph: dict[str, Any] | None = None,
        applied_rules: list[str] | None = None,
        iteration_count: int = 1,
        errors: list[str] | None = None,
    ):
        self.success = success
        self.modified_graph = modified_graph or {}
        self.applied_rules = applied_rules or []
        self.iteration_count = iteration_count
        self.errors = errors or []

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to a JSON-safe dict."""
        return {
            "success": self.success,
            "applied_rules": self.applied_rules,
            "iteration_count": self.iteration_count,
            "errors": self.errors,
        }


class RewriteEngine:
    """Engine that registers and applies rewrite rules.

    Usage::

        engine = RewriteEngine()
        engine.register_rule(my_rule)

        # Single pass
        result = engine.apply_all(graph)

        # Fixpoint
        result = engine.apply_fixpoint(graph, max_iterations=10)
    """

    def __init__(self) -> None:
        self._rules: dict[str, RewriteRule] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_rule(self, rule: RewriteRule) -> None:
        """Register a single rewrite rule.

        Raises:
            ValueError: If a rule with the same *name* is already registered.
        """
        if rule.name in self._rules:
            raise ValueError(f"Rule '{rule.name}' is already registered.")
        self._rules[rule.name] = rule
        logger.debug("Registered rewrite rule '%s' (v%s)", rule.name, rule.version)

    def register_rules(self, rules: list[RewriteRule]) -> None:
        """Register multiple rules at once."""
        for rule in rules:
            self.register_rule(rule)

    def unregister_rule(self, name: str) -> None:
        """Remove a rule by name (no-op if not found)."""
        self._rules.pop(name, None)

    def get_rule(self, name: str) -> RewriteRule | None:
        """Look up a registered rule by name."""
        return self._rules.get(name)

    def list_rules(self) -> list[dict[str, Any]]:
        """Return metadata dicts for all registered rules, sorted by priority."""
        sorted_rules = sorted(self._rules.values(), key=lambda r: r.priority)
        return [r.to_dict() for r in sorted_rules]

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------

    def apply_rule(self, rule_name: str, graph: dict[str, Any]) -> RewriteResult:
        """Apply a single named rule once.

        Args:
            rule_name: Name of the registered rule.
            graph:     Input IR graph dict (not modified in place).

        Returns:
            A :class:`RewriteResult`.  The *modified_graph* is a deep copy
            even if the condition was false (no-op).
        """
        rule = self._rules.get(rule_name)
        if rule is None:
            return RewriteResult(
                success=False,
                modified_graph=copy.deepcopy(graph),
                errors=[f"Rule '{rule_name}' not found."],
            )

        try:
            result_graph = rule(graph)
            if result_graph is None:
                # Condition was false → no change
                return RewriteResult(
                    success=True,
                    modified_graph=copy.deepcopy(graph),
                    applied_rules=[],
                )
            return RewriteResult(
                success=True,
                modified_graph=result_graph,
                applied_rules=[rule_name],
            )
        except Exception as exc:
            logger.exception("Rule '%s' raised an exception", rule_name)
            return RewriteResult(
                success=False,
                modified_graph=copy.deepcopy(graph),
                errors=[f"Rule '{rule_name}' failed: {exc}"],
            )

    def apply_all(self, graph: dict[str, Any]) -> RewriteResult:
        """Apply every enabled rule once, in priority order.

        Rules are applied sequentially.  Each rule sees the output of the
        previous rule.
        """
        current = copy.deepcopy(graph)
        applied: list[str] = []
        errors: list[str] = []

        sorted_rules = sorted(
            (r for r in self._rules.values() if r.enabled),
            key=lambda r: r.priority,
        )

        for rule in sorted_rules:
            try:
                result = rule(current)
                if result is not None:
                    current = result
                    applied.append(rule.name)
            except Exception as exc:
                logger.exception("Rule '%s' raised an exception", rule.name)
                errors.append(f"Rule '{rule.name}' failed: {exc}")

        return RewriteResult(
            success=len(errors) == 0,
            modified_graph=current,
            applied_rules=applied,
            iteration_count=1,
            errors=errors,
        )

    def apply_fixpoint(
        self,
        graph: dict[str, Any],
        max_iterations: int = 10,
    ) -> RewriteResult:
        """Apply rules repeatedly until no rule changes the graph.

        The fixpoint loop:
        1. Run all enabled rules in priority order.
        2. If at least one rule fired and changed the graph, repeat.
        3. Stop when no rule fires or *max_iterations* is reached.

        Args:
            graph:           Input IR graph dict.
            max_iterations:  Safety limit to prevent infinite loops (default 10).

        Returns:
            A :class:`RewriteResult` with the stabilised graph.
        """
        current = copy.deepcopy(graph)
        all_applied: list[str] = []
        all_errors: list[str] = []

        sorted_rules = sorted(
            (r for r in self._rules.values() if r.enabled),
            key=lambda r: r.priority,
        )

        for iteration in range(max_iterations):
            changed = False
            for rule in sorted_rules:
                try:
                    result = rule(current)
                    if result is not None:
                        current = result
                        all_applied.append(rule.name)
                        changed = True
                except Exception as exc:
                    logger.exception("Rule '%s' raised an exception", rule.name)
                    all_errors.append(f"Rule '{rule.name}' failed: {exc}")

            if not changed:
                logger.debug(
                    "Fixpoint reached after %d iteration(s) with %d rule(s) applied.",
                    iteration + 1,
                    len(all_applied),
                )
                return RewriteResult(
                    success=len(all_errors) == 0,
                    modified_graph=current,
                    applied_rules=all_applied,
                    iteration_count=iteration + 1,
                    errors=all_errors,
                )

        logger.warning(
            "Fixpoint did not converge after %d iterations "
            "(rules may form a cycle). Applied: %s",
            max_iterations,
            all_applied,
        )
        return RewriteResult(
            success=False,
            modified_graph=current,
            applied_rules=all_applied,
            iteration_count=max_iterations,
            errors=all_errors
            + [f"Fixpoint did not converge after {max_iterations} iterations."],
        )
