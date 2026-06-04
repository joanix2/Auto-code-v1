"""Inheritance Service — merge, trace, and resolve graph inheritance.

This service provides operations for defining and resolving inheritance
relationships between IR graphs.  Inheritance allows a child graph to
reuse nodes, edges, and rules from one or more parent graphs.

Key operations:
- ``set_parent`` / ``get_parent`` — manage single parent link
- ``resolve_inheritance`` — merge a child graph with its parent
- ``get_inherited_nodes`` / ``get_inherited_edges`` — selective merge
- ``get_inheritance_chain`` — trace multi-level parent chain
- ``get_element_origin`` — determine if an element is local or inherited
- ``get_multiple_parents`` / ``resolve_multiple_inheritance`` — multi-parent

All methods operate on standard IR JSON graph dicts
(``{metadata, nodes, edges}``) and are pure — they never modify inputs.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from src.services.inheritance.inheritance_models import (
    InheritanceConfig,
    InheritanceTree,
    InheritanceType,
    InheritedElement,
)

logger = logging.getLogger(__name__)

# Metadata field names used to store inheritance links
PARENT_ID_FIELD = "parent_id"
PARENT_IDS_FIELD = "parent_ids"
INHERITANCE_TYPE_FIELD = "inheritance_type"

# Standard IR JSON keys
META_KEY = "metadata"
NODES_KEY = "nodes"
EDGES_KEY = "edges"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_graph_id(graph_data: dict[str, Any]) -> str:
    """Extract the graph ID from an IR JSON graph dict."""
    meta = graph_data.get(META_KEY, {})
    return str(meta.get("id", ""))


def _clone_graph(graph_data: dict[str, Any]) -> dict[str, Any]:
    """Deep-clone an IR JSON graph dict so mutations never affect the original."""
    return copy.deepcopy(graph_data)


def _build_id_index(
    items: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build an ``{item_id: item}`` index from a list of dicts with an ``id`` key."""
    return {item["id"]: item for item in items if "id" in item}


def _collect_ids(items: list[dict[str, Any]]) -> set[str]:
    """Collect all 'id' values from a list of dicts."""
    return {item["id"] for item in items if "id" in item}


def _is_edge_dict(item: dict[str, Any]) -> bool:
    """Heuristic: an edge dict has source/target keys, a node dict does not."""
    return "source" in item and "target" in item


# ---------------------------------------------------------------------------
# InheritanceService
# ---------------------------------------------------------------------------


class InheritanceService:
    """Stateless service for graph inheritance operations.

    All methods accept standard IR JSON graph dicts and return new
    dicts or metadata; inputs are never mutated.
    """

    # ------------------------------------------------------------------
    # Parent management
    # ------------------------------------------------------------------

    @staticmethod
    def set_parent(
        child_graph_data: dict[str, Any],
        parent_graph_data: dict[str, Any],
        inheritance_type: InheritanceType = InheritanceType.FULL,
    ) -> dict[str, Any]:
        """Set the parent for a child graph.

        Returns a new graph dict with ``parent_id`` set in metadata.
        The original ``child_graph_data`` is not modified.

        Args:
            child_graph_data: The child IR graph dict.
            parent_graph_data: The parent IR graph dict (its ID is recorded).
            inheritance_type: The type of inheritance to apply.

        Returns:
            A new graph dict with inheritance metadata added.
        """
        parent_id = _get_graph_id(parent_graph_data)
        child_id = _get_graph_id(child_graph_data)

        if not parent_id:
            raise ValueError("Parent graph has no valid 'id' in metadata")

        if parent_id == child_id:
            raise ValueError("A graph cannot be its own parent")

        result = _clone_graph(child_graph_data)
        meta = result.setdefault(META_KEY, {})
        meta[PARENT_ID_FIELD] = parent_id
        meta[INHERITANCE_TYPE_FIELD] = inheritance_type.value
        return result

    @staticmethod
    def get_parent(
        graph_data: dict[str, Any],
    ) -> str | None:
        """Get the parent ID recorded in a graph's metadata.

        Args:
            graph_data: An IR graph dict.

        Returns:
            Parent graph ID if set, else None.
        """
        meta = graph_data.get(META_KEY, {})
        return meta.get(PARENT_ID_FIELD)

    @staticmethod
    def clear_parent(graph_data: dict[str, Any]) -> dict[str, Any]:
        """Remove the parent link from a graph's metadata.

        Args:
            graph_data: An IR graph dict.

        Returns:
            A new graph dict without parent metadata.
        """
        result = _clone_graph(graph_data)
        meta = result.get(META_KEY, {})
        meta.pop(PARENT_ID_FIELD, None)
        meta.pop(INHERITANCE_TYPE_FIELD, None)
        return result

    # ------------------------------------------------------------------
    # Single inheritance resolution
    # ------------------------------------------------------------------

    @staticmethod
    def get_inherited_nodes(
        child_graph_data: dict[str, Any],
        parent_graph_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Get all nodes from parent merged with child.

        Child nodes override parent nodes with the same ID.
        The resulting list contains every node from the parent plus
        any additional nodes from the child.

        Args:
            child_graph_data: The child IR graph dict.
            parent_graph_data: The parent IR graph dict.

        Returns:
            Merged list of node dicts.
        """
        parent_nodes = parent_graph_data.get(NODES_KEY, [])
        child_nodes = child_graph_data.get(NODES_KEY, [])

        # Build index: start with parent, then override with child
        merged = _build_id_index(parent_nodes)
        for node in child_nodes:
            merged[node["id"]] = node

        return list(merged.values())

    @staticmethod
    def get_inherited_edges(
        child_graph_data: dict[str, Any],
        parent_graph_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Get all edges from parent merged with child.

        Child edges override parent edges with the same ID.
        Edge references are NOT re-validated here (caller should validate).

        Args:
            child_graph_data: The child IR graph dict.
            parent_graph_data: The parent IR graph dict.

        Returns:
            Merged list of edge dicts.
        """
        parent_edges = parent_graph_data.get(EDGES_KEY, [])
        child_edges = child_graph_data.get(EDGES_KEY, [])

        merged = _build_id_index(parent_edges)
        for edge in child_edges:
            merged[edge["id"]] = edge

        return list(merged.values())

    @staticmethod
    def get_inherited_rules(
        child_graph_data: dict[str, Any],
        parent_graph_data: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Get rules from the parent graph.

        Rules are nodes/edges tagged with a ``_rule`` flag or belonging
        to a ``rule`` type.  Returns an empty list if the parent has none.

        Args:
            child_graph_data: The child IR graph dict (unused in this impl.
                              but kept for API consistency).
            parent_graph_data: The parent IR graph dict.

        Returns:
            List of rule node/edge dicts from the parent.
        """
        # Rules can be identified in two ways:
        # 1. Nodes with type "rule" or node_type.name == "rule"
        # 2. Nodes/edges with a "_rule": true flag
        rules: list[dict[str, Any]] = []

        for node in parent_graph_data.get(NODES_KEY, []):
            if node.get("type") == "rule" or node.get("_rule") is True:
                rules.append(node)

        for edge in parent_graph_data.get(EDGES_KEY, []):
            if edge.get("type") == "rule" or edge.get("_rule") is True:
                rules.append(edge)

        return rules

    @staticmethod
    def resolve_inheritance(
        child_graph_data: dict[str, Any],
        parent_graph_data: dict[str, Any],
        inheritance_type: InheritanceType = InheritanceType.OVERRIDE,
    ) -> dict[str, Any]:
        """Resolve full inheritance: merge parent into child.

        For **OVERRIDE** inheritance, child elements with the same ID as
        a parent element replace the parent version.

        For **FULL** inheritance, the same merge occurs (all parent
        elements are included).

        For **PARTIAL** inheritance, only parent elements that are
        referenced by child edges are included (not yet fully implemented:
        currently falls back to FULL behavior).

        The result is a complete IR graph dict suitable for validation,
        querying, or rendering.

        Args:
            child_graph_data: The child IR graph dict.
            parent_graph_data: The parent IR graph dict.
            inheritance_type: Inheritance mode (default OVERRIDE).

        Returns:
            A new merged IR graph dict.
        """
        result = _clone_graph(child_graph_data)

        inherited_nodes = InheritanceService.get_inherited_nodes(
            child_graph_data, parent_graph_data
        )
        inherited_edges = InheritanceService.get_inherited_edges(
            child_graph_data, parent_graph_data
        )

        result[NODES_KEY] = inherited_nodes
        result[EDGES_KEY] = inherited_edges

        # Update counts
        meta = result.setdefault(META_KEY, {})
        meta["node_count"] = len(inherited_nodes)
        meta["edge_count"] = len(inherited_edges)

        # Merge edgeConstraints from parent if present
        parent_constraints = parent_graph_data.get("edgeConstraints", [])
        child_constraints = child_graph_data.get("edgeConstraints", [])
        # Child constraints override parent ones with same edgeType
        constraint_map = {c.get("edgeType"): c for c in parent_constraints}
        for c in child_constraints:
            constraint_map[c.get("edgeType")] = c
        result["edgeConstraints"] = list(constraint_map.values())

        # Merge allowed_node_types and allowed_edge_types from parent
        parent_meta = parent_graph_data.get(META_KEY, {})
        if "allowed_node_types" in parent_meta:
            existing = {
                nt["name"] for nt in meta.get("allowed_node_types", [])
            }
            for nt in parent_meta["allowed_node_types"]:
                if nt["name"] not in existing:
                    meta.setdefault("allowed_node_types", []).append(nt)

        if "allowed_edge_types" in parent_meta:
            existing = {
                et["name"] for et in meta.get("allowed_edge_types", [])
            }
            for et in parent_meta["allowed_edge_types"]:
                if et["name"] not in existing:
                    meta.setdefault("allowed_edge_types", []).append(et)

        return result

    # ------------------------------------------------------------------
    # Inheritance chain
    # ------------------------------------------------------------------

    @staticmethod
    def get_inheritance_chain(
        graph_data: dict[str, Any],
        all_graphs: dict[str, dict[str, Any]],
        max_depth: int = 20,
    ) -> list[InheritanceTree]:
        """Get the inheritance chain from the given graph up to the root.

        Builds a list of ``InheritanceTree`` nodes representing the chain
        from the current graph up to the root ancestor.

        Args:
            graph_data: The starting IR graph dict.
            all_graphs: A mapping of ``{graph_id: graph_dict}`` for all
                        available graphs in the system.
            max_depth: Maximum number of levels to traverse (default 20).
                       Prevents infinite loops from circular references.

        Returns:
            List of ``InheritanceTree`` nodes ordered from the starting
            graph up to the root.

        Raises:
            ValueError: If a circular inheritance is detected.
        """
        chain: list[InheritanceTree] = []
        visited: set[str] = set()
        current = graph_data
        depth = 0

        while depth <= max_depth:
            graph_id = _get_graph_id(current)
            if not graph_id:
                break

            if graph_id in visited:
                raise ValueError(
                    f"Circular inheritance detected at graph '{graph_id}'"
                )
            visited.add(graph_id)

            parent_id = InheritanceService.get_parent(current)
            meta = current.get(META_KEY, {})
            inh_type_str = meta.get(INHERITANCE_TYPE_FIELD)
            inh_type = (
                InheritanceType(inh_type_str) if inh_type_str else None
            )

            chain.append(
                InheritanceTree(
                    graph_id=graph_id,
                    parent_id=parent_id,
                    depth=depth,
                    inheritance_type=inh_type,
                )
            )

            if not parent_id or parent_id not in all_graphs:
                break

            current = all_graphs[parent_id]
            depth += 1

        return chain

    # ------------------------------------------------------------------
    # Element origin tracing
    # ------------------------------------------------------------------

    @staticmethod
    def get_element_origin(
        element_id: str,
        child_graph_data: dict[str, Any],
        parent_graph_data: dict[str, Any],
        all_graphs: dict[str, dict[str, Any]] | None = None,
        max_depth: int = 20,
    ) -> InheritedElement | None:
        """Trace the origin of an element (node or edge) by ID.

        Determines whether the element:
        - Is **local** (defined only in the child, depth=0)
        - Is **inherited** from parent (defined in parent, not in child)
        - Is **overridden** (defined in both, child version wins)

        When ``all_graphs`` is provided, the method walks the full
        inheritance chain to find the deepest origin.

        Args:
            element_id: The element (node or edge) ID to trace.
            child_graph_data: The child IR graph dict.
            parent_graph_data: The parent IR graph dict.
            all_graphs: Optional mapping of ``{graph_id: graph_dict}``
                        for multi-level tracing.
            max_depth: Maximum levels to traverse.

        Returns:
            An ``InheritedElement`` describing the origin, or None if the
            element is not found in either graph.
        """
        # Check child
        child_node_ids = _collect_ids(child_graph_data.get(NODES_KEY, []))
        child_edge_ids = _collect_ids(child_graph_data.get(EDGES_KEY, []))
        in_child_nodes = element_id in child_node_ids
        in_child_edges = element_id in child_edge_ids

        # Check parent
        parent_node_ids = _collect_ids(parent_graph_data.get(NODES_KEY, []))
        parent_edge_ids = _collect_ids(parent_graph_data.get(EDGES_KEY, []))
        in_parent_nodes = element_id in parent_node_ids
        in_parent_edges = element_id in parent_edge_ids

        # Determine element type
        element_type: str | None = None
        if in_child_nodes or in_parent_nodes:
            element_type = "node"
        elif in_child_edges or in_parent_edges:
            element_type = "edge"
        else:
            # Not found in either — try the chain
            if all_graphs:
                return InheritanceService._trace_origin_chain(
                    element_id=element_id,
                    graph_data=child_graph_data,
                    all_graphs=all_graphs,
                    visited=None,
                    depth=0,
                    max_depth=max_depth,
                )
            return None

        is_overridden = (in_child_nodes and in_parent_nodes) or (
            in_child_edges and in_parent_edges
        )

        local_mods: dict[str, Any] = {}
        if is_overridden and element_type:
            # Compute the diff between child and parent versions
            source_list = (
                child_graph_data.get(NODES_KEY, [])
                if element_type == "node"
                else child_graph_data.get(EDGES_KEY, [])
            )
            parent_list = (
                parent_graph_data.get(NODES_KEY, [])
                if element_type == "node"
                else parent_graph_data.get(EDGES_KEY, [])
            )
            child_item = _build_id_index(source_list).get(element_id, {})
            parent_item = _build_id_index(parent_list).get(element_id, {})
            for k, v in child_item.items():
                if k != "id" and parent_item.get(k) != v:
                    local_mods[k] = v

        source_graph_id = _get_graph_id(
            child_graph_data if in_child_nodes or in_child_edges else parent_graph_data
        )

        return InheritedElement(
            element_id=element_id,
            element_type=element_type,
            source_graph_id=source_graph_id,
            is_overridden=is_overridden,
            local_modifications=local_mods,
            depth=0 if (in_child_nodes or in_child_edges) else 1,
        )

    @staticmethod
    def _trace_origin_chain(
        element_id: str,
        graph_data: dict[str, Any],
        all_graphs: dict[str, dict[str, Any]],
        visited: set[str] | None,
        depth: int,
        max_depth: int,
    ) -> InheritedElement | None:
        """Recursively trace element origin up the inheritance chain."""
        if visited is None:
            visited = set()
        if depth > max_depth:
            return None

        graph_id = _get_graph_id(graph_data)
        if not graph_id or graph_id in visited:
            return None
        visited.add(graph_id)

        # Check if element exists in this graph
        node_ids = _collect_ids(graph_data.get(NODES_KEY, []))
        edge_ids = _collect_ids(graph_data.get(EDGES_KEY, []))
        in_nodes = element_id in node_ids
        in_edges = element_id in edge_ids

        if in_nodes or in_edges:
            element_type = "node" if in_nodes else "edge"
            return InheritedElement(
                element_id=element_id,
                element_type=element_type,
                source_graph_id=graph_id,
                is_overridden=False,
                local_modifications={},
                depth=depth,
            )

        # Walk up to parent
        parent_id = InheritanceService.get_parent(graph_data)
        if parent_id and parent_id in all_graphs:
            return InheritanceService._trace_origin_chain(
                element_id=element_id,
                graph_data=all_graphs[parent_id],
                all_graphs=all_graphs,
                visited=visited,
                depth=depth + 1,
                max_depth=max_depth,
            )

        return None

    # ------------------------------------------------------------------
    # Multiple inheritance
    # ------------------------------------------------------------------

    @staticmethod
    def set_multiple_parents(
        child_graph_data: dict[str, Any],
        parent_graphs: list[dict[str, Any]],
        inheritance_type: InheritanceType = InheritanceType.FULL,
    ) -> dict[str, Any]:
        """Set multiple parents for a child graph.

        The first parent in the list has the highest priority for conflict
        resolution (first parent wins on conflicts).

        Args:
            child_graph_data: The child IR graph dict.
            parent_graphs: Ordered list of parent IR graph dicts.
                           First = highest priority.
            inheritance_type: The type of inheritance to apply.

        Returns:
            A new graph dict with ``parent_ids`` in metadata.

        Raises:
            ValueError: If any parent graph has no valid ID.
        """
        child_id = _get_graph_id(child_graph_data)
        parent_ids: list[str] = []
        for pg in parent_graphs:
            pid = _get_graph_id(pg)
            if not pid:
                raise ValueError("A parent graph has no valid 'id' in metadata")
            if pid == child_id:
                raise ValueError("A graph cannot be its own parent")
            parent_ids.append(pid)

        result = _clone_graph(child_graph_data)
        meta = result.setdefault(META_KEY, {})
        meta[PARENT_IDS_FIELD] = parent_ids
        meta[INHERITANCE_TYPE_FIELD] = inheritance_type.value

        # Also set the first parent as the primary parent_id
        if parent_ids:
            meta[PARENT_ID_FIELD] = parent_ids[0]

        return result

    @staticmethod
    def get_multiple_parents(
        graph_data: dict[str, Any],
        all_graphs: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Get all parent graph dicts for a given graph.

        Checks both ``parent_ids`` (multi) and ``parent_id`` (single)
        metadata fields.

        Args:
            graph_data: An IR graph dict.
            all_graphs: Mapping of ``{graph_id: graph_dict}``.

        Returns:
            Ordered list of parent graph dicts.
        """
        meta = graph_data.get(META_KEY, {})
        parent_ids: list[str] = meta.get(PARENT_IDS_FIELD, [])

        # Fallback to single parent_id
        single = meta.get(PARENT_ID_FIELD)
        if single and single not in parent_ids:
            parent_ids.insert(0, single)

        parents: list[dict[str, Any]] = []
        for pid in parent_ids:
            parent = all_graphs.get(pid)
            if parent is not None:
                parents.append(parent)
            else:
                logger.warning("Parent graph '%s' not found in all_graphs", pid)

        return parents

    @staticmethod
    def resolve_multiple_inheritance(
        child_graph_data: dict[str, Any],
        parent_graphs: list[dict[str, Any]],
        inheritance_type: InheritanceType = InheritanceType.OVERRIDE,
    ) -> dict[str, Any]:
        """Merge a child graph with multiple parents.

        Conflict resolution strategy:
        1. Child elements always win over any parent.
        2. For conflicts between parents, the first parent in the list
           (highest priority) wins.
        3. Elements unique to lower-priority parents are still included.

        Args:
            child_graph_data: The child IR graph dict.
            parent_graphs: Ordered list of parent IR graph dicts.
                           First = highest priority.
            inheritance_type: Inheritance mode (default OVERRIDE).

        Returns:
            A new merged IR graph dict.
        """
        if not parent_graphs:
            return _clone_graph(child_graph_data)

        # Start with the child
        result = _clone_graph(child_graph_data)

        # Conflict resolution:
        # 1. First parent (highest priority) wins over other parents
        # 2. Child always wins over any parent
        node_index: dict[str, dict[str, Any]] = {}
        # Process parents in normal order — first parent establishes the base
        for parent in parent_graphs:
            for node in parent.get(NODES_KEY, []):
                nid = node.get("id")
                if nid and nid not in node_index:
                    node_index[nid] = node
        # Child overrides all
        for node in child_graph_data.get(NODES_KEY, []):
            node_index[node["id"]] = node

        # Same for edges
        edge_index: dict[str, dict[str, Any]] = {}
        for parent in parent_graphs:
            for edge in parent.get(EDGES_KEY, []):
                eid = edge.get("id")
                if eid and eid not in edge_index:
                    edge_index[eid] = edge
        for edge in child_graph_data.get(EDGES_KEY, []):
            edge_index[edge["id"]] = edge

        result[NODES_KEY] = list(node_index.values())
        result[EDGES_KEY] = list(edge_index.values())

        # Update counts
        meta = result.setdefault(META_KEY, {})
        meta["node_count"] = len(result[NODES_KEY])
        meta["edge_count"] = len(result[EDGES_KEY])

        # Merge edgeConstraints from all parents
        constraint_map: dict[str, Any] = {}
        for parent in parent_graphs:
            for c in parent.get("edgeConstraints", []):
                et = c.get("edgeType")
                if et and et not in constraint_map:
                    constraint_map[et] = c
        # Child constraints override
        for c in child_graph_data.get("edgeConstraints", []):
            constraint_map[c.get("edgeType")] = c
        result["edgeConstraints"] = list(constraint_map.values())

        # Merge allowed types from parents
        existing_node_types = {
            nt["name"]
            for nt in meta.get("allowed_node_types", [])
        }
        for parent in parent_graphs:
            pmeta = parent.get(META_KEY, {})
            for nt in pmeta.get("allowed_node_types", []):
                if nt["name"] not in existing_node_types:
                    meta.setdefault("allowed_node_types", []).append(nt)
                    existing_node_types.add(nt["name"])

        existing_edge_types = {
            et["name"]
            for et in meta.get("allowed_edge_types", [])
        }
        for parent in parent_graphs:
            pmeta = parent.get(META_KEY, {})
            for et in pmeta.get("allowed_edge_types", []):
                if et["name"] not in existing_edge_types:
                    meta.setdefault("allowed_edge_types", []).append(et)
                    existing_edge_types.add(et["name"])

        return result

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def find_graph_by_id(
        graph_id: str,
        all_graphs: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Find a graph dict by its ID in the all_graphs mapping.

        Args:
            graph_id: The graph ID to look up.
            all_graphs: Mapping of ``{graph_id: graph_dict}``.

        Returns:
            The graph dict if found, else None.
        """
        return all_graphs.get(graph_id)
