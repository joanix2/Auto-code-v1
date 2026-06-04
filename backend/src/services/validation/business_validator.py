"""Business Rule Validator — enforces domain-specific constraints on the IR graph.

Rules implemented:
1. **Cardinality validation** — checks that no node exceeds a maximum number
   of incident edges of a given type.
2. **Cycle detection** — detects forbidden cycles based on edge types
   (e.g. SUBCLASS_OF cycles are typically invalid).
3. **Domain-specific rules** — an extensible hook for custom rule functions.
"""

from __future__ import annotations

from typing import Any, Callable

from src.services.validation.validation_report import Severity, ValidationError, ValidationReport

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

# A domain-specific rule is a callable that receives the full graph dict and
# returns a (possibly empty) list of ValidationError.
DomainRule = Callable[[dict[str, Any]], list[ValidationError]]

# ---------------------------------------------------------------------------
# Built-in business rules
# ---------------------------------------------------------------------------

# Edge types that are known to form a hierarchy where cycles are forbidden.
ACYCLIC_EDGE_TYPES = {"SUBCLASS_OF", "IS_A"}

# Default maximum number of edges of a particular type per node.
DEFAULT_MAX_CARDINALITY: int = 100


def validate_cardinalities(
    data: dict[str, Any],
    max_cardinality: int = DEFAULT_MAX_CARDINALITY,
) -> ValidationReport:
    """Check that no node exceeds *max_cardinality* edges of the same type.

    This is a generic cardinality guard to catch accidental "star" explosions.
    Overly large fan-outs usually indicate a modelling mistake.

    Args:
        data: The IR graph dict.
        max_cardinality: Maximum number of incident edges (in + out) of the
            same type per node.
    """
    report = ValidationReport()

    # Count edge occurrences by (node_id, edge_type)
    from collections import Counter

    counter: Counter[tuple[str, str]] = Counter()
    for edge in data.get("edges", []):
        src = edge.get("source")
        tgt = edge.get("target")
        etype = edge.get("type")
        if src:
            counter[(src, etype)] += 1
        if tgt:
            counter[(tgt, etype)] += 1

    for (node_id, etype), count in counter.items():
        if count > max_cardinality:
            report.add_error(
                ValidationError(
                    code="CARDINALITY_EXCEEDED",
                    message=f"Node '{node_id}' has {count} edges of type '{etype}', "
                    f"which exceeds the maximum of {max_cardinality}.",
                    severity=Severity.WARNING,
                    location=node_id,
                    suggestion=f"Consider reducing the number of '{etype}' edges on '{node_id}' "
                    f"to at most {max_cardinality}.",
                )
            )
    return report


def detect_forbidden_cycles(
    data: dict[str, Any],
    acyclic_types: set[str] | None = None,
) -> ValidationReport:
    """Detect cycles formed by edges whose type is in *acyclic_types*.

    Uses DFS-based cycle detection over the subgraph induced by those edge
    types.

    Args:
        data: The IR graph dict.
        acyclic_types: Set of edge type strings that must not form cycles.
            Defaults to ``{"SUBCLASS_OF", "IS_A"}``.
    """
    report = ValidationReport()
    if acyclic_types is None:
        acyclic_types = ACYCLIC_EDGE_TYPES

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Build adjacency list for acyclic edge types (directed)
    adj: dict[str, list[str]] = {n.get("id", ""): [] for n in nodes if n.get("id")}
    for edge in edges:
        etype = edge.get("type")
        src = edge.get("source")
        tgt = edge.get("target")
        if etype and etype.upper() in {t.upper() for t in acyclic_types} and src and tgt:
            adj.setdefault(src, []).append(tgt)

    node_ids = list(adj.keys())

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {nid: WHITE for nid in node_ids}
    parent: dict[str, str | None] = {nid: None for nid in node_ids}
    cycle_found = False

    def dfs(u: str) -> None:
        nonlocal cycle_found
        if cycle_found:
            return
        color[u] = GRAY
        for v in adj.get(u, []):
            if v not in color:
                # v is not in the graph at all — skip
                continue
            if color[v] == GRAY:
                cycle_found = True
                # Reconstruct the cycle path
                path = [v, u]
                cur = u
                while cur != v and parent.get(cur) is not None:
                    cur = parent[cur]  # type: ignore[assignment]
                    if cur is not None:
                        path.append(cur)
                path.reverse()
                path_str = " → ".join(path)
                report.add_error(
                    ValidationError(
                        code="FORBIDDEN_CYCLE",
                        message=f"Forbidden cycle detected with acyclic edge types "
                        f"{sorted(acyclic_types)}: {path_str}.",
                        severity=Severity.ERROR,
                        location=v,
                        suggestion="Break the cycle by removing or reorienting one of the edges "
                        "in the cycle path.",
                    )
                )
                return
            if color[v] == WHITE:
                parent[v] = u
                dfs(v)
        color[u] = BLACK

    for nid in node_ids:
        if color[nid] == WHITE:
            dfs(nid)
            if cycle_found:
                break

    return report


# ---------------------------------------------------------------------------
# Domain-specific rule registry
# ---------------------------------------------------------------------------

_DOMAIN_RULES: list[DomainRule] = []


def register_domain_rule(rule: DomainRule) -> None:
    """Register a custom domain-specific rule function.

    The rule will be called by :func:`run_business_validators` with the full
    graph dict.  It must return a list of :class:`ValidationError`.
    """
    _DOMAIN_RULES.append(rule)


def clear_domain_rules() -> None:
    """Remove all registered domain rules (useful in tests)."""
    _DOMAIN_RULES.clear()


def get_domain_rules() -> list[DomainRule]:
    """Return the list of currently registered domain rules."""
    return list(_DOMAIN_RULES)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_business_validators(data: dict[str, Any]) -> ValidationReport:
    """Run all business-rule validators and return the aggregated report.

    Includes:
    - Cardinality validation
    - Forbidden-cycle detection
    - Every function registered via :func:`register_domain_rule`
    """
    report = ValidationReport()
    report.merge(validate_cardinalities(data))
    report.merge(detect_forbidden_cycles(data))

    for rule in _DOMAIN_RULES:
        try:
            errors = rule(data)
            report.add_errors(errors)
        except Exception as exc:
            report.add_error(
                ValidationError(
                    code="DOMAIN_RULE_ERROR",
                    message=f"Domain rule {rule.__name__!r} raised an exception: {exc}",
                    severity=Severity.ERROR,
                    location="",
                    suggestion="Fix the domain rule implementation or the graph data.",
                )
            )
    return report
