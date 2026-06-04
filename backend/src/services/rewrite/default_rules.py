"""Default rewrite rules bundled with the engine.

Rules:
1. **normalize_names** — strip whitespace from all node/edge ``name`` fields.
2. **remove_orphan_edges** — delete edges whose ``source`` or ``target`` node
   does not exist in the graph.
3. **deduplicate_nodes** — merge nodes with identical ``name`` **and** ``type``;
   keep the first occurrence, rewire edges to point to the survivor.
4. **infer_missing_labels** — for nodes with an empty or missing ``label``,
   set it from ``name``.
"""

from __future__ import annotations

import copy
from typing import Any

from src.services.rewrite.rewrite_rule import RewriteRule


# ---------------------------------------------------------------------------
# Helper: build a node id → node lookup
# ---------------------------------------------------------------------------


def _node_map(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {n.get("id", ""): n for n in graph.get("nodes", []) if n.get("id")}


# ---------------------------------------------------------------------------
# Condition / Action for each rule
# ---------------------------------------------------------------------------


def _has_whitespace_in_name(graph: dict[str, Any]) -> bool:
    """True if any node or edge has leading/trailing whitespace in its name."""
    for node in graph.get("nodes", []):
        name = node.get("name", "")
        if isinstance(name, str) and name != name.strip():
            return True
    for edge in graph.get("edges", []):
        name = edge.get("name", "")
        if isinstance(name, str) and name != name.strip():
            return True
    return False


def _normalize_names_action(graph: dict[str, Any]) -> dict[str, Any]:
    """Strip leading/trailing whitespace from all name fields."""
    result = copy.deepcopy(graph)
    for node in result.get("nodes", []):
        if "name" in node and isinstance(node["name"], str):
            node["name"] = node["name"].strip()
    for edge in result.get("edges", []):
        if "name" in edge and isinstance(edge["name"], str):
            edge["name"] = edge["name"].strip()
        if "label" in edge and isinstance(edge["label"], str):
            edge["label"] = edge["label"].strip()
    return result


# ---------------------------------------------------------------------------


def _has_orphan_edges(graph: dict[str, Any]) -> bool:
    """True if any edge references a non-existent source or target node."""
    node_ids = {n.get("id", "") for n in graph.get("nodes", []) if n.get("id")}
    for edge in graph.get("edges", []):
        src = edge.get("source")
        tgt = edge.get("target")
        if (src and src not in node_ids) or (tgt and tgt not in node_ids):
            return True
    return False


def _remove_orphan_edges_action(graph: dict[str, Any]) -> dict[str, Any]:
    """Remove edges whose source or target node doesn't exist."""
    node_ids = {n.get("id", "") for n in graph.get("nodes", []) if n.get("id")}
    result = copy.deepcopy(graph)
    result["edges"] = [
        e
        for e in result.get("edges", [])
        if e.get("source") in node_ids and e.get("target") in node_ids
    ]
    return result


# ---------------------------------------------------------------------------


def _has_duplicate_nodes(graph: dict[str, Any]) -> bool:
    """True if at least two nodes share the same ``name`` + ``type``."""
    seen: set[tuple[str, str]] = set()
    for node in graph.get("nodes", []):
        key = (node.get("name", ""), node.get("type", ""))
        if key in seen:
            return True
        seen.add(key)
    return False


def _deduplicate_nodes_action(graph: dict[str, Any]) -> dict[str, Any]:
    """Merge duplicate nodes (same name+type). Keep first, rewire edges."""
    result = copy.deepcopy(graph)
    seen: dict[tuple[str, str], str] = {}  # (name, type) → survivor id
    survivors: list[dict[str, Any]] = []
    removed_ids: set[str] = set()

    for node in result.get("nodes", []):
        key = (node.get("name", ""), node.get("type", ""))
        if key in seen:
            removed_ids.add(node.get("id", ""))
        else:
            seen[key] = node.get("id", "")
            survivors.append(node)

    # Rewire edges that pointed to a removed node
    for edge in result.get("edges", []):
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        # Find survivors for removed ids
        for removed_id in removed_ids:
            # Find which key this removed_id maps from
            for key, sid in seen.items():
                if removed_id == sid:
                    continue
            # Actually simpler: build a reverse map
            pass

    # Build a direct removal → survivor mapping
    removed_to_survivor: dict[str, str] = {}
    for node in graph.get("nodes", []):
        key = (node.get("name", ""), node.get("type", ""))
        nid = node.get("id", "")
        # The survivor is the first occurrence
        if nid not in removed_ids:
            continue
        # Find the survivor id for this key
        survivor_id = seen.get(key)
        if survivor_id and survivor_id != nid:
            removed_to_survivor[nid] = survivor_id

    # Rewire edges
    for edge in result.get("edges", []):
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src in removed_to_survivor:
            edge["source"] = removed_to_survivor[src]
        if tgt in removed_to_survivor:
            edge["target"] = removed_to_survivor[tgt]

    result["nodes"] = survivors
    return result


# ---------------------------------------------------------------------------


def _has_missing_labels(graph: dict[str, Any]) -> bool:
    """True if any node is missing its ``label`` field or has an empty label."""
    for node in graph.get("nodes", []):
        label = node.get("label")
        if not label:
            return True
    return False


def _infer_missing_labels_action(graph: dict[str, Any]) -> dict[str, Any]:
    """Set ``label`` from ``name`` for nodes that lack a label."""
    result = copy.deepcopy(graph)
    for node in result.get("nodes", []):
        if not node.get("label") and node.get("name"):
            node["label"] = node["name"]
    for edge in result.get("edges", []):
        if not edge.get("label") and edge.get("name"):
            edge["label"] = edge["name"]
    return result


# ---------------------------------------------------------------------------
# Default rule instances
# ---------------------------------------------------------------------------

NORMALIZE_NAMES = RewriteRule(
    name="normalize_names",
    description="Trim leading and trailing whitespace from all node/edge name fields.",
    condition=_has_whitespace_in_name,
    action=_normalize_names_action,
    priority=10,
)

REMOVE_ORPHAN_EDGES = RewriteRule(
    name="remove_orphan_edges",
    description="Remove edges whose source or target node does not exist in the graph.",
    condition=_has_orphan_edges,
    action=_remove_orphan_edges_action,
    priority=20,
)

DEDUPLICATE_NODES = RewriteRule(
    name="deduplicate_nodes",
    description="Merge nodes with identical name and type; keep the first occurrence and rewire edges.",
    condition=_has_duplicate_nodes,
    action=_deduplicate_nodes_action,
    priority=30,
)

INFER_MISSING_LABELS = RewriteRule(
    name="infer_missing_labels",
    description="Set default display labels from node/edge names when labels are missing.",
    condition=_has_missing_labels,
    action=_infer_missing_labels_action,
    priority=40,
)

# Ordered list suitable for bulk registration
DEFAULT_RULES: list[RewriteRule] = [
    NORMALIZE_NAMES,
    REMOVE_ORPHAN_EDGES,
    DEDUPLICATE_NODES,
    INFER_MISSING_LABELS,
]
