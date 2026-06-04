"""Pattern Matcher — find subgraphs matching a structural specification.

The pattern specification follows a simple JSON format::

    {
        "nodes": {
            "a": {"type": "concept", "name": None},   # None = wildcard
            "b": {"type": "attribute"},
        },
        "edges": [
            {"source": "a", "target": "b", "type": "HAS_ATTRIBUTE"},
        ],
        "conditions": [
            {"field": "a.name", "op": "startswith", "value": "T"},  # optional
        ]
    }

Wildcard matching:
- A value of ``None`` in a node spec matches any value.
- ``"*"`` as an edge type matches any edge type.
- Omitting a field means "match any".
"""

from __future__ import annotations

import operator
from typing import Any

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def match_pattern(
    graph: dict[str, Any],
    pattern_spec: dict[str, Any],
) -> list[dict[str, Any]]:
    """Find all subgraphs in *graph* that match *pattern_spec*.

    Args:
        graph:        An IR graph dict (with ``nodes`` and ``edges`` lists).
        pattern_spec: A dict with keys ``nodes``, ``edges``, and optionally
                      ``conditions`` (see module docstring for format).

    Returns:
        A list of match dicts.  Each match maps alias → node dict.
        Returns an empty list when there are no matches.
    """
    node_specs = pattern_spec.get("nodes", {})
    edge_specs = pattern_spec.get("edges", [])
    conditions = pattern_spec.get("conditions", [])

    if not node_specs:
        return []

    graph_nodes = graph.get("nodes", [])
    graph_edges = graph.get("edges", [])

    # Build a lookup for fast node access by id
    nodes_by_id: dict[str, dict[str, Any]] = {
        n.get("id", ""): n for n in graph_nodes if n.get("id")
    }

    # ------------------------------------------------------------------
    # 1. Find candidate sets of node ids for each alias
    # ------------------------------------------------------------------
    candidates: dict[str, list[str]] = {}
    for alias, spec in node_specs.items():
        cids: list[str] = []
        for n in graph_nodes:
            nid = n.get("id", "")
            if not nid:
                continue
            if _node_matches(n, spec):
                cids.append(nid)
        candidates[alias] = cids

    # If any alias has zero candidates → no match
    if any(len(cids) == 0 for cids in candidates.values()):
        return []

    # ------------------------------------------------------------------
    # 2. Enumerate valid alias→id assignments via backtracking
    # ------------------------------------------------------------------
    aliases = list(node_specs.keys())
    matches: list[dict[str, str]] = []  # list of {alias: id} assignments

    def _backtrack(idx: int, assignment: dict[str, str]) -> None:
        if idx == len(aliases):
            matches.append(dict(assignment))
            return

        alias = aliases[idx]
        for nid in candidates[alias]:
            if nid in assignment.values():
                continue  # each node can appear at most once per match
            assignment[alias] = nid

            # Check edge constraints for all *complete* pairs so far
            if _edges_satisfied(assignment, edge_specs, graph_edges):
                _backtrack(idx + 1, assignment)

            del assignment[alias]

    _backtrack(0, {})

    # ------------------------------------------------------------------
    # 3. Build result dicts (alias → full node dict)
    # ------------------------------------------------------------------
    results: list[dict[str, Any]] = []
    for assignment in matches:
        match: dict[str, Any] = {}
        ok = True
        for alias, nid in assignment.items():
            match[alias] = nodes_by_id.get(nid, {})
        # Filter by extra conditions
        if _satisfies_conditions(match, conditions, graph_edges):
            results.append(match)

    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _node_matches(node: dict[str, Any], spec: dict[str, Any]) -> bool:
    """Check if a single node matches a type/name spec."""
    for key, expected in spec.items():
        actual = node.get(key)
        if expected is None:
            # None = wildcard (match anything including missing)
            continue
        if isinstance(expected, str) and expected.startswith("__re:"):
            # Regex match
            import re

            if not re.match(expected[5:], str(actual or "")):
                return False
        elif actual != expected:
            return False
    return True


def _edges_satisfied(
    assignment: dict[str, str],
    edge_specs: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> bool:
    """Check that every edge spec whose aliases are both assigned exists."""
    for spec in edge_specs:
        src_alias = spec.get("source", "")
        tgt_alias = spec.get("target", "")
        if src_alias not in assignment or tgt_alias not in assignment:
            continue  # not all aliases assigned yet → skip

        src_id = assignment[src_alias]
        tgt_id = assignment[tgt_alias]
        expected_type = spec.get("type", "*")
        expected_dir = spec.get("direction", "outgoing")

        found = False
        for edge in graph_edges:
            if expected_dir == "incoming":
                if edge.get("source") != tgt_id or edge.get("target") != src_id:
                    continue
            else:
                if edge.get("source") != src_id or edge.get("target") != tgt_id:
                    continue

            if expected_type != "*" and edge.get("type") != expected_type:
                continue
            found = True
            break

        if not found:
            return False
    return True


def _satisfies_conditions(
    match: dict[str, Any],
    conditions: list[dict[str, Any]],
    graph_edges: list[dict[str, Any]],
) -> bool:
    """Evaluate post-match conditions (field comparisons)."""
    for cond in conditions:
        field = cond.get("field", "")
        op_name = cond.get("op", "eq")
        value = cond.get("value")

        # Resolve field path: "a.name" or "a.type"
        parts = field.split(".", 1)
        if len(parts) != 2:
            continue
        alias, attr = parts
        node = match.get(alias, {})
        actual = node.get(attr)

        op_fn = _OPERATORS.get(op_name)
        if op_fn is None:
            continue

        if not op_fn(actual, value):
            return False
    return True


# Supported comparison operators
_OPERATORS: dict[str, Any] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "ge": operator.ge,
    "lt": operator.lt,
    "le": operator.le,
    "startswith": lambda a, b: isinstance(a, str) and a.startswith(b),
    "endswith": lambda a, b: isinstance(a, str) and a.endswith(b),
    "contains": lambda a, b: isinstance(a, str) and b in a,
    "in": lambda a, b: isinstance(b, (list, tuple)) and a in b,
    "regex": lambda a, b: __import__("re").match(b, str(a)) is not None,
    "exists": lambda a, _: a is not None,
    "not_exists": lambda a, _: a is None,
}
