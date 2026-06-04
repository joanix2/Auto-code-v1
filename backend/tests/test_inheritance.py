"""Tests for the Inheritance and Composition System (MVP E).

Tests cover:
1. Inheritance models — Pydantic creation, enum values, serialization
2. Single inheritance — parent → child merging
3. Override behavior — child overrides parent on ID conflict
4. Multiple inheritance — conflict resolution (first parent wins)
5. Inheritance chain — grandparent → parent → child resolution
6. API endpoints — set-parent, inherited, chain, origin, parents
7. Edge cases — circular inheritance, no parent, self-parent

Key design:
- ``InheritanceService`` is pure-stateless (all static methods)
- Tests use pure dict IR graphs (no Neo4j required for unit tests)
- API tests use TestClient with the in-memory controller store
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.services.inheritance import (
    InheritanceConfig,
    InheritanceService,
    InheritanceTree,
    InheritanceType,
    InheritedElement,
)

# ---------------------------------------------------------------------------
# Fixtures: sample IR graph dicts
# ---------------------------------------------------------------------------


@pytest.fixture
def graph_parent() -> dict[str, Any]:
    """A parent graph with 2 nodes and 1 edge."""
    return {
        "metadata": {
            "id": "graph-parent-1",
            "name": "Parent Graph",
            "version": "1.0.0",
            "node_count": 2,
            "edge_count": 1,
            "allowed_node_types": [
                {
                    "name": "concept",
                    "label": "Concept",
                    "labelPlural": "Concepts",
                    "gender": "m",
                    "article": "le",
                }
            ],
            "allowed_edge_types": [
                {
                    "name": "SUBCLASS_OF",
                    "sourceNodeTypes": ["concept"],
                    "targetNodeTypes": ["concept"],
                    "directed": True,
                }
            ],
        },
        "nodes": [
            {"id": "n1", "name": "Vehicle", "type": "concept"},
            {"id": "n2", "name": "Engine", "type": "concept"},
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "type": "HAS_COMPONENT",
            }
        ],
    }


@pytest.fixture
def graph_child() -> dict[str, Any]:
    """A child graph with 2 nodes (one overriding parent) and 1 new edge."""
    return {
        "metadata": {
            "id": "graph-child-1",
            "name": "Child Graph",
            "version": "1.0.0",
            "node_count": 2,
            "edge_count": 1,
        },
        "nodes": [
            {"id": "n1", "name": "Vehicle (Overridden)", "type": "concept"},  # overrides parent n1
            {"id": "n3", "name": "Wheel", "type": "concept"},  # new node
        ],
        "edges": [
            {
                "id": "e2",
                "source": "n1",
                "target": "n3",
                "type": "HAS_COMPONENT",
            }
        ],
    }


@pytest.fixture
def graph_grandparent() -> dict[str, Any]:
    """A grandparent graph with 1 node."""
    return {
        "metadata": {
            "id": "graph-grandparent-1",
            "name": "Grandparent Graph",
            "version": "1.0.0",
        },
        "nodes": [
            {"id": "n0", "name": "Root", "type": "concept"},
        ],
        "edges": [],
    }


@pytest.fixture
def graph_parent2() -> dict[str, Any]:
    """A second parent graph for multi-inheritance testing."""
    return {
        "metadata": {
            "id": "graph-parent-2",
            "name": "Parent Graph 2",
            "version": "1.0.0",
        },
        "nodes": [
            {"id": "n4", "name": "Color", "type": "attribute"},
        ],
        "edges": [],
    }


@pytest.fixture
def graph_empty() -> dict[str, Any]:
    """An empty graph with only metadata."""
    return {
        "metadata": {"id": "graph-empty", "name": "Empty", "version": "1.0.0"},
        "nodes": [],
        "edges": [],
    }


# ---------------------------------------------------------------------------
# Test: Inheritance Models
# ---------------------------------------------------------------------------


class TestInheritanceModels:
    """Tests for the Pydantic inheritance models."""

    def test_inheritance_type_enum(self):
        assert InheritanceType.FULL.value == "FULL"
        assert InheritanceType.PARTIAL.value == "PARTIAL"
        assert InheritanceType.OVERRIDE.value == "OVERRIDE"
        assert len(InheritanceType) == 3

    def test_inheritance_config_creation(self):
        config = InheritanceConfig(
            parent_id="p1",
            child_id="c1",
            inheritance_type=InheritanceType.FULL,
            description="Test inheritance",
        )
        assert config.parent_id == "p1"
        assert config.child_id == "c1"
        assert config.inheritance_type == InheritanceType.FULL
        assert config.description == "Test inheritance"

    def test_inheritance_config_default_type(self):
        config = InheritanceConfig(parent_id="p1", child_id="c1")
        assert config.inheritance_type == InheritanceType.FULL

    def test_inheritance_config_serialization(self):
        config = InheritanceConfig(
            parent_id="p1",
            child_id="c1",
            inheritance_type=InheritanceType.PARTIAL,
        )
        data = config.model_dump()
        assert data["parent_id"] == "p1"
        assert data["child_id"] == "c1"
        assert data["inheritance_type"] == "PARTIAL"

    def test_inheritance_tree_creation(self):
        tree = InheritanceTree(
            graph_id="g1",
            parent_id=None,
            depth=0,
            child_ids=["g2", "g3"],
        )
        assert tree.graph_id == "g1"
        assert tree.parent_id is None
        assert tree.depth == 0
        assert tree.child_ids == ["g2", "g3"]

    def test_inheritance_tree_with_inheritance_type(self):
        tree = InheritanceTree(
            graph_id="g2",
            parent_id="g1",
            depth=1,
            inheritance_type=InheritanceType.FULL,
        )
        assert tree.inheritance_type == InheritanceType.FULL

    def test_inherited_element_creation(self):
        elem = InheritedElement(
            element_id="n1",
            element_type="node",
            source_graph_id="graph-parent-1",
            is_overridden=True,
            local_modifications={"name": "Overridden"},
        )
        assert elem.element_id == "n1"
        assert elem.element_type == "node"
        assert elem.is_overridden is True
        assert elem.local_modifications == {"name": "Overridden"}
        assert elem.depth == 0

    def test_inherited_element_depth(self):
        elem = InheritedElement(
            element_id="n1",
            element_type="node",
            source_graph_id="grandparent",
            depth=2,
        )
        assert elem.depth == 2
        assert elem.is_overridden is False

    def test_inherited_element_serialization(self):
        elem = InheritedElement(
            element_id="n1",
            element_type="node",
            source_graph_id="g1",
        )
        data = elem.model_dump()
        assert data["element_id"] == "n1"
        assert data["element_type"] == "node"
        assert data["is_overridden"] is False
        assert data["local_modifications"] == {}
        assert data["depth"] == 0

    def test_inheritance_type_from_string(self):
        assert InheritanceType("FULL") == InheritanceType.FULL
        assert InheritanceType("PARTIAL") == InheritanceType.PARTIAL
        assert InheritanceType("OVERRIDE") == InheritanceType.OVERRIDE

    def test_invalid_inheritance_type(self):
        with pytest.raises(ValueError):
            InheritanceType("INVALID")


# ---------------------------------------------------------------------------
# Test: Inheritance Service — Parent Management
# ---------------------------------------------------------------------------


class TestParentManagement:
    """Tests for set_parent, get_parent, clear_parent."""

    def test_set_parent_adds_metadata(self, graph_child, graph_parent):
        result = InheritanceService.set_parent(
            graph_child, graph_parent, InheritanceType.FULL
        )
        assert result["metadata"]["parent_id"] == "graph-parent-1"
        assert result["metadata"]["inheritance_type"] == "FULL"

    def test_set_parent_does_not_mutate_input(self, graph_child, graph_parent):
        original = copy.deepcopy(graph_child)
        InheritanceService.set_parent(graph_child, graph_parent)
        assert graph_child == original  # unchanged

    def test_get_parent_returns_none_when_not_set(self, graph_child):
        assert InheritanceService.get_parent(graph_child) is None

    def test_get_parent_after_set(self, graph_child, graph_parent):
        child = InheritanceService.set_parent(graph_child, graph_parent)
        assert InheritanceService.get_parent(child) == "graph-parent-1"

    def test_clear_parent(self, graph_child, graph_parent):
        child = InheritanceService.set_parent(graph_child, graph_parent)
        cleared = InheritanceService.clear_parent(child)
        assert InheritanceService.get_parent(cleared) is None

    def test_set_parent_raises_on_missing_parent_id(self, graph_child):
        invalid_parent = {"metadata": {"name": "No ID"}, "nodes": [], "edges": []}
        with pytest.raises(ValueError, match="no valid 'id'"):
            InheritanceService.set_parent(graph_child, invalid_parent)


# ---------------------------------------------------------------------------
# Test: Inheritance Service — Single Inheritance Resolution
# ---------------------------------------------------------------------------


class TestSingleInheritance:
    """Tests for single inheritance merging."""

    def test_get_inherited_nodes_merges_both(self, graph_child, graph_parent):
        nodes = InheritanceService.get_inherited_nodes(graph_child, graph_parent)
        ids = {n["id"] for n in nodes}
        assert "n1" in ids  # from both (child overrides)
        assert "n2" in ids  # from parent only
        assert "n3" in ids  # from child only

    def test_get_inherited_nodes_child_overrides(self, graph_child, graph_parent):
        nodes = InheritanceService.get_inherited_nodes(graph_child, graph_parent)
        n1 = next(n for n in nodes if n["id"] == "n1")
        assert n1["name"] == "Vehicle (Overridden)"  # child wins

    def test_get_inherited_edges_merges_both(self, graph_child, graph_parent):
        edges = InheritanceService.get_inherited_edges(graph_child, graph_parent)
        ids = {e["id"] for e in edges}
        assert "e1" in ids  # from parent
        assert "e2" in ids  # from child

    def test_get_inherited_rules_from_parent(self, graph_parent):
        # Add a rule node to the parent
        parent = copy.deepcopy(graph_parent)
        parent["nodes"].append({"id": "r1", "name": "Rule1", "type": "rule"})
        rules = InheritanceService.get_inherited_rules({}, parent)
        assert len(rules) == 1
        assert rules[0]["id"] == "r1"

    def test_get_inherited_rules_empty(self, graph_parent):
        rules = InheritanceService.get_inherited_rules({}, graph_parent)
        assert rules == []

    def test_get_inherited_rules_with_flag(self, graph_parent):
        parent = copy.deepcopy(graph_parent)
        parent["nodes"].append({"id": "x1", "name": "X", "_rule": True})
        rules = InheritanceService.get_inherited_rules({}, parent)
        assert any(r["id"] == "x1" for r in rules)

    def test_resolve_inheritance_merges_everything(self, graph_child, graph_parent):
        merged = InheritanceService.resolve_inheritance(
            graph_child, graph_parent, InheritanceType.OVERRIDE
        )
        assert len(merged["nodes"]) == 3  # n1, n2, n3
        assert len(merged["edges"]) == 2  # e1, e2

        # Check node count updated
        assert merged["metadata"]["node_count"] == 3
        assert merged["metadata"]["edge_count"] == 2

    def test_resolve_inheritance_child_overrides(self, graph_child, graph_parent):
        merged = InheritanceService.resolve_inheritance(
            graph_child, graph_parent, InheritanceType.OVERRIDE
        )
        n1 = next(n for n in merged["nodes"] if n["id"] == "n1")
        assert n1["name"] == "Vehicle (Overridden)"

    def test_resolve_inheritance_preserves_child_metadata(self, graph_child, graph_parent):
        merged = InheritanceService.resolve_inheritance(graph_child, graph_parent)
        assert merged["metadata"]["id"] == "graph-child-1"
        assert merged["metadata"]["name"] == "Child Graph"

    def test_resolve_inheritance_merges_allowed_types(self, graph_child, graph_parent):
        merged = InheritanceService.resolve_inheritance(graph_child, graph_parent)
        assert len(merged["metadata"]["allowed_node_types"]) == 1
        assert merged["metadata"]["allowed_node_types"][0]["name"] == "concept"

    def test_resolve_full_inheritance_vs_partial(self, graph_child, graph_parent):
        """Both FULL and OVERRIDE produce the same merged result for non-conflicting."""
        full_merged = InheritanceService.resolve_inheritance(
            graph_child, graph_parent, InheritanceType.FULL
        )
        override_merged = InheritanceService.resolve_inheritance(
            graph_child, graph_parent, InheritanceType.OVERRIDE
        )
        assert len(full_merged["nodes"]) == len(override_merged["nodes"])
        assert len(full_merged["edges"]) == len(override_merged["edges"])


# ---------------------------------------------------------------------------
# Test: Inheritance Chain
# ---------------------------------------------------------------------------


class TestInheritanceChain:
    """Tests for multi-level inheritance chain resolution."""

    def test_chain_no_parent(self, graph_child, graph_parent):
        all_graphs = {"graph-child-1": graph_child}
        chain = InheritanceService.get_inheritance_chain(graph_child, all_graphs)
        assert len(chain) == 1
        assert chain[0].graph_id == "graph-child-1"
        assert chain[0].parent_id is None

    def test_chain_one_parent(self, graph_child, graph_parent):
        child = InheritanceService.set_parent(graph_child, graph_parent)
        all_graphs = {
            "graph-child-1": child,
            "graph-parent-1": graph_parent,
        }
        chain = InheritanceService.get_inheritance_chain(child, all_graphs)
        assert len(chain) == 2
        assert chain[0].graph_id == "graph-child-1"
        assert chain[0].depth == 0
        assert chain[1].graph_id == "graph-parent-1"
        assert chain[1].depth == 1

    def test_chain_two_levels(
        self, graph_child, graph_parent, graph_grandparent
    ):
        # Build chain: grandparent -> parent -> child
        parent = InheritanceService.set_parent(
            graph_parent, graph_grandparent
        )
        child = InheritanceService.set_parent(graph_child, parent)

        all_graphs = {
            "graph-child-1": child,
            "graph-parent-1": parent,
            "graph-grandparent-1": graph_grandparent,
        }
        chain = InheritanceService.get_inheritance_chain(child, all_graphs)
        assert len(chain) == 3
        assert chain[0].graph_id == "graph-child-1"
        assert chain[0].depth == 0
        assert chain[1].graph_id == "graph-parent-1"
        assert chain[1].depth == 1
        assert chain[1].parent_id == "graph-grandparent-1"
        assert chain[2].graph_id == "graph-grandparent-1"
        assert chain[2].depth == 2
        assert chain[2].parent_id is None

    def test_chain_circular_detection(self, graph_child, graph_parent):
        # Set parent -> child, then try to make parent a child of child
        child = InheritanceService.set_parent(graph_child, graph_parent)
        circular_parent = InheritanceService.set_parent(graph_parent, child)  # type: ignore[arg-type]

        all_graphs = {
            "graph-child-1": child,
            "graph-parent-1": circular_parent,
        }

        with pytest.raises(ValueError, match="Circular inheritance"):
            InheritanceService.get_inheritance_chain(child, all_graphs)

    def test_chain_max_depth_limit(self, graph_child, graph_parent):
        # Deep chain with limited depth
        all_graphs = {
            "graph-child-1": InheritanceService.set_parent(
                graph_child, graph_parent
            ),
            "graph-parent-1": graph_parent,
        }
        # max_depth=1 should only go 1 level
        chain = InheritanceService.get_inheritance_chain(
            all_graphs["graph-child-1"], all_graphs, max_depth=1
        )
        # current graph (depth 0) + parent (depth 1) = 2 nodes
        assert len(chain) <= 2


# ---------------------------------------------------------------------------
# Test: Element Origin Tracing
# ---------------------------------------------------------------------------


class TestElementOrigin:
    """Tests for tracing element origin."""

    def test_origin_local_node(self, graph_child, graph_parent):
        origin = InheritanceService.get_element_origin(
            "n3", graph_child, graph_parent
        )
        assert origin is not None
        assert origin.element_id == "n3"
        assert origin.source_graph_id == "graph-child-1"
        assert origin.depth == 0
        assert origin.is_overridden is False

    def test_origin_inherited_node(self, graph_child, graph_parent):
        origin = InheritanceService.get_element_origin(
            "n2", graph_child, graph_parent
        )
        assert origin is not None
        assert origin.element_id == "n2"
        assert origin.source_graph_id == "graph-parent-1"
        assert origin.depth == 1
        assert origin.is_overridden is False

    def test_origin_overridden_node(self, graph_child, graph_parent):
        origin = InheritanceService.get_element_origin(
            "n1", graph_child, graph_parent
        )
        assert origin is not None
        assert origin.element_id == "n1"
        assert origin.is_overridden is True
        assert "name" in origin.local_modifications

    def test_origin_not_found(self, graph_child, graph_parent):
        origin = InheritanceService.get_element_origin(
            "nonexistent", graph_child, graph_parent
        )
        assert origin is None

    def test_origin_chain_tracing(
        self, graph_child, graph_parent, graph_grandparent
    ):
        # Elements defined only in grandparent should be traced there
        parent = InheritanceService.set_parent(
            graph_parent, graph_grandparent
        )
        child = InheritanceService.set_parent(graph_child, parent)

        all_graphs = {
            "graph-child-1": child,
            "graph-parent-1": parent,
            "graph-grandparent-1": graph_grandparent,
        }

        origin = InheritanceService.get_element_origin(
            "n0", child, parent, all_graphs=all_graphs
        )
        assert origin is not None
        assert origin.element_id == "n0"
        assert origin.source_graph_id == "graph-grandparent-1"
        assert origin.depth == 2

    def test_origin_edge(self, graph_child, graph_parent):
        parent_edge_id = "e1"
        origin = InheritanceService.get_element_origin(
            parent_edge_id, graph_child, graph_parent
        )
        assert origin is not None
        assert origin.element_id == parent_edge_id
        assert origin.element_type == "edge"


# ---------------------------------------------------------------------------
# Test: Multiple Inheritance
# ---------------------------------------------------------------------------


class TestMultipleInheritance:
    """Tests for multiple parent inheritance."""

    def test_set_multiple_parents(self, graph_child, graph_parent, graph_parent2):
        result = InheritanceService.set_multiple_parents(
            graph_child,
            [graph_parent, graph_parent2],
            InheritanceType.FULL,
        )
        assert result["metadata"]["parent_ids"] == [
            "graph-parent-1",
            "graph-parent-2",
        ]
        assert result["metadata"]["parent_id"] == "graph-parent-1"  # primary

    def test_get_multiple_parents(self, graph_child, graph_parent, graph_parent2):
        child = InheritanceService.set_multiple_parents(
            graph_child, [graph_parent, graph_parent2]
        )
        all_graphs = {
            "graph-child-1": child,
            "graph-parent-1": graph_parent,
            "graph-parent-2": graph_parent2,
        }
        parents = InheritanceService.get_multiple_parents(child, all_graphs)
        assert len(parents) == 2
        assert _get_id(parents[0]) == "graph-parent-1"
        assert _get_id(parents[1]) == "graph-parent-2"

    def test_get_multiple_parents_with_single_fallback(self, graph_child, graph_parent):
        """When only parent_id is set (not parent_ids), should still work."""
        child = InheritanceService.set_parent(graph_child, graph_parent)
        all_graphs = {
            "graph-child-1": child,
            "graph-parent-1": graph_parent,
        }
        parents = InheritanceService.get_multiple_parents(child, all_graphs)
        assert len(parents) == 1
        assert _get_id(parents[0]) == "graph-parent-1"

    def test_resolve_multiple_inheritance_basic(
        self, graph_child, graph_parent, graph_parent2
    ):
        merged = InheritanceService.resolve_multiple_inheritance(
            graph_child,
            [graph_parent, graph_parent2],
        )
        # Should have nodes from child (n1, n3) + parent (n2) + parent2 (n4)
        ids = {n["id"] for n in merged["nodes"]}
        assert "n1" in ids
        assert "n2" in ids
        assert "n3" in ids
        assert "n4" in ids

    def test_resolve_multiple_inheritance_child_wins(
        self, graph_child, graph_parent, graph_parent2
    ):
        merged = InheritanceService.resolve_multiple_inheritance(
            graph_child,
            [graph_parent, graph_parent2],
        )
        n1 = next(n for n in merged["nodes"] if n["id"] == "n1")
        assert n1["name"] == "Vehicle (Overridden)"  # child wins over parent

    def test_resolve_multiple_inheritance_first_parent_wins_on_conflict(
        self, graph_parent, graph_parent2
    ):
        """Both parents have node 'n1' with different names.
        First parent should win."""
        p1 = copy.deepcopy(graph_parent)
        p2 = copy.deepcopy(graph_parent2)
        # Add conflicting node n1 in both parents
        p1["nodes"] = [
            {"id": "n1", "name": "From Parent 1", "type": "concept"}
        ]
        p2["nodes"] = [
            {"id": "n1", "name": "From Parent 2", "type": "concept"}
        ]

        empty_child = {
            "metadata": {"id": "child", "name": "Child", "version": "1.0.0"},
            "nodes": [],
            "edges": [],
        }

        merged = InheritanceService.resolve_multiple_inheritance(
            empty_child, [p1, p2]
        )
        n1 = next(n for n in merged["nodes"] if n["id"] == "n1")
        assert n1["name"] == "From Parent 1"  # first parent wins

    def test_resolve_multiple_inheritance_empty_parents(self, graph_child):
        merged = InheritanceService.resolve_multiple_inheritance(
            graph_child, []
        )
        assert len(merged["nodes"]) == len(graph_child["nodes"])

    def test_resolve_multiple_inheritance_three_parents(
        self, graph_empty, graph_parent, graph_parent2
    ):
        p3 = {
            "metadata": {"id": "p3", "name": "P3", "version": "1.0.0"},
            "nodes": [{"id": "n5", "name": "From P3", "type": "concept"}],
            "edges": [],
        }
        merged = InheritanceService.resolve_multiple_inheritance(
            graph_empty, [graph_parent, graph_parent2, p3]
        )
        ids = {n["id"] for n in merged["nodes"]}
        assert "n1" in ids
        assert "n2" in ids
        assert "n4" in ids
        assert "n5" in ids

    def test_set_multiple_parents_raises_on_missing_id(self, graph_child):
        invalid_parent = {"metadata": {}, "nodes": [], "edges": []}
        with pytest.raises(ValueError, match="no valid 'id'"):
            InheritanceService.set_multiple_parents(
                graph_child, [invalid_parent]
            )


# ---------------------------------------------------------------------------
# Test: Integration — Full chain resolution
# ---------------------------------------------------------------------------


class TestFullChainResolution:
    """Integration tests for multi-level chain with resolve_inheritance."""

    def test_two_level_chain(
        self, graph_child, graph_parent, graph_grandparent
    ):
        # grandparent -> parent -> child
        parent = InheritanceService.set_parent(
            graph_parent, graph_grandparent
        )

        # Resolve grandparent into parent
        merged_parent = InheritanceService.resolve_inheritance(
            parent, graph_grandparent, InheritanceType.OVERRIDE
        )
        assert len(merged_parent["nodes"]) == 3  # n0 + n1 + n2
        assert "n0" in {n["id"] for n in merged_parent["nodes"]}

        # Then resolve parent + grandparent into child
        child = InheritanceService.set_parent(graph_child, merged_parent)
        merged_child = InheritanceService.resolve_inheritance(
            child, merged_parent, InheritanceType.OVERRIDE
        )
        assert len(merged_child["nodes"]) == 4  # n0 + n1 + n2 + n3
        ids = {n["id"] for n in merged_child["nodes"]}
        assert ids == {"n0", "n1", "n2", "n3"}

        # n1 should still be overridden by child
        n1 = next(n for n in merged_child["nodes"] if n["id"] == "n1")
        assert n1["name"] == "Vehicle (Overridden)"

    def test_three_level_chain_elements_inherited(self):
        """Verify elements from grandparent show through to child."""
        gp = {
            "metadata": {"id": "gp", "name": "GP", "version": "1.0.0"},
            "nodes": [{"id": "a", "name": "Alpha", "type": "concept"}],
            "edges": [],
        }
        p = {
            "metadata": {"id": "p", "name": "P", "version": "1.0.0"},
            "nodes": [{"id": "b", "name": "Beta", "type": "concept"}],
            "edges": [],
        }
        c = {
            "metadata": {"id": "c", "name": "C", "version": "1.0.0"},
            "nodes": [{"id": "c1", "name": "Gamma", "type": "concept"}],
            "edges": [],
        }

        p_with_parent = InheritanceService.set_parent(p, gp)
        c_with_parent = InheritanceService.set_parent(c, p_with_parent)

        p_merged = InheritanceService.resolve_inheritance(
            p_with_parent, gp, InheritanceType.OVERRIDE
        )
        c_merged = InheritanceService.resolve_inheritance(
            c_with_parent, p_merged, InheritanceType.OVERRIDE
        )

        ids = {n["id"] for n in c_merged["nodes"]}
        assert ids == {"a", "b", "c1"}


# ---------------------------------------------------------------------------
# Test: Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_no_parent_scenario(self, graph_child):
        # Graph with no parent should raise no errors
        parent_id = InheritanceService.get_parent(graph_child)
        assert parent_id is None

    def test_empty_graph_inheritance(self, graph_empty, graph_parent):
        # Empty child inheriting from parent should get parent's nodes
        merged = InheritanceService.resolve_inheritance(
            graph_empty, graph_parent
        )
        assert len(merged["nodes"]) == 2
        assert len(merged["edges"]) == 1

    def test_self_parent_rejection(self):
        with pytest.raises(ValueError, match="cannot be its own parent"):
            InheritanceService.set_parent(
                {"metadata": {"id": "x"}, "nodes": [], "edges": []},
                {"metadata": {"id": "x"}, "nodes": [], "edges": []},
            )

    def test_parent_with_empty_nodes_and_edges(self, graph_child):
        empty_parent = {
            "metadata": {"id": "empty-parent", "name": "Empty", "version": "1.0.0"},
            "nodes": [],
            "edges": [],
        }
        merged = InheritanceService.resolve_inheritance(
            graph_child, empty_parent
        )
        # Child should be unchanged
        assert len(merged["nodes"]) == len(graph_child["nodes"])
        assert len(merged["edges"]) == len(graph_child["edges"])

    def test_resolve_inheritance_with_no_parent_id_in_parent(self, graph_child):
        # Parent with no metadata id
        bad_parent = {"metadata": {}, "nodes": [], "edges": []}
        with pytest.raises(ValueError, match="no valid 'id'"):
            InheritanceService.set_parent(graph_child, bad_parent)

    def test_multiple_inheritance_child_wins_all_parents(
        self, graph_parent, graph_parent2
    ):
        """Child nodes should override the same IDs in ANY parent."""
        p1 = copy.deepcopy(graph_parent)
        p2 = copy.deepcopy(graph_parent2)

        p1["nodes"] = [{"id": "shared", "name": "From P1", "type": "concept"}]
        p2["nodes"] = [{"id": "shared", "name": "From P2", "type": "concept"}]

        child = {
            "metadata": {"id": "child", "name": "C", "version": "1.0.0"},
            "nodes": [
                {"id": "shared", "name": "From Child", "type": "concept"}
            ],
            "edges": [],
        }

        merged = InheritanceService.resolve_multiple_inheritance(
            child, [p1, p2]
        )
        shared = next(n for n in merged["nodes"] if n["id"] == "shared")
        assert shared["name"] == "From Child"  # child always wins

    def test_get_element_origin_none_for_unknown(self, graph_child, graph_parent):
        origin = InheritanceService.get_element_origin(
            "unknown-id", graph_child, graph_parent
        )
        assert origin is None

    def test_empty_graph_clear_parent(self, graph_empty):
        # clearing parent on graph with no parent should be a no-op
        result = InheritanceService.clear_parent(graph_empty)
        assert InheritanceService.get_parent(result) is None
        # should also have no inheritance_type in metadata
        assert "inheritance_type" not in result.get("metadata", {})


# ---------------------------------------------------------------------------
# Test: API Endpoints
# ---------------------------------------------------------------------------


class TestInheritanceAPI:
    """Tests for the /api/inheritance/ REST endpoints."""

    def test_set_parent_endpoint(self, client: TestClient):
        payload = {
            "config": {
                "parent_id": "graph-p",
                "child_id": "graph-c",
                "inheritance_type": "FULL",
            },
        }
        response = client.post("/api/inheritance/set-parent", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Parent set successfully"
        assert data["config"]["parent_id"] == "graph-p"
        assert data["config"]["child_id"] == "graph-c"

    def test_set_parent_with_graph_data(self, client: TestClient):
        payload = {
            "config": {
                "parent_id": "gp-api-1",
                "child_id": "gc-api-1",
                "inheritance_type": "OVERRIDE",
            },
            "child_graph": {
                "metadata": {"id": "gc-api-1", "name": "Child", "version": "1.0.0"},
                "nodes": [{"id": "n1", "name": "Local", "type": "concept"}],
                "edges": [],
            },
            "parent_graph": {
                "metadata": {"id": "gp-api-1", "name": "Parent", "version": "1.0.0"},
                "nodes": [
                    {"id": "n0", "name": "Inherited", "type": "concept"}
                ],
                "edges": [],
            },
        }
        response = client.post("/api/inheritance/set-parent", json=payload)
        assert response.status_code == 200

        # Now check the inherited graph
        resp2 = client.get("/api/inheritance/gc-api-1/inherited")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["inherited"] is True
        ids = {n["id"] for n in data2["graph"]["nodes"]}
        assert ids == {"n0", "n1"}

    def test_get_inherited_no_parent(self, client: TestClient):
        # Register a graph with NO parent link at all
        client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "orphan-parent",
                    "child_id": "orphan-child",
                    "inheritance_type": "FULL",
                },
                "child_graph": {
                    "metadata": {
                        "id": "orphan-child",
                        "name": "Orphan",
                        "version": "1.0.0",
                    },
                    "nodes": [],
                    "edges": [],
                },
            },
        )

        # Parent "orphan-parent" has no full graph data, but is referenced
        resp = client.get("/api/inheritance/orphan-child/inherited")
        assert resp.status_code == 200
        data = resp.json()
        # Inheritance resolves (parent is known), with empty parent data
        assert data["inherited"] is True

    def test_get_inherited_not_found(self, client: TestClient):
        response = client.get("/api/inheritance/does-not-exist/inherited")
        assert response.status_code == 404

    def test_get_chain_endpoint(self, client: TestClient):
        # Set up a chain
        client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "gp-chain-grandparent",
                    "child_id": "gp-chain-parent",
                    "inheritance_type": "FULL",
                },
            },
        )
        client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "gp-chain-parent",
                    "child_id": "gp-chain-child",
                    "inheritance_type": "FULL",
                },
            },
        )

        response = client.get("/api/inheritance/gp-chain-child/chain")
        assert response.status_code == 200
        data = response.json()
        assert data["graph_id"] == "gp-chain-child"
        assert data["length"] >= 2

    def test_get_chain_not_found(self, client: TestClient):
        response = client.get("/api/inheritance/no-such-graph/chain")
        assert response.status_code == 404

    def test_get_origin_endpoint(self, client: TestClient):
        # Register with graph data
        payload = {
            "config": {
                "parent_id": "gp-origin-parent",
                "child_id": "gp-origin-child",
                "inheritance_type": "OVERRIDE",
            },
            "child_graph": {
                "metadata": {
                    "id": "gp-origin-child",
                    "name": "Child",
                    "version": "1.0.0",
                },
                "nodes": [
                    {"id": "local", "name": "Local", "type": "concept"}
                ],
                "edges": [],
            },
            "parent_graph": {
                "metadata": {
                    "id": "gp-origin-parent",
                    "name": "Parent",
                    "version": "1.0.0",
                },
                "nodes": [
                    {"id": "inherited", "name": "Inherited", "type": "concept"}
                ],
                "edges": [],
            },
        }
        client.post("/api/inheritance/set-parent", json=payload)

        # Check origin of inherited element
        resp = client.get(
            "/api/inheritance/gp-origin-child/origin/inherited"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_graph_id"] == "gp-origin-parent"
        assert data["depth"] == 1
        assert data["is_overridden"] is False

        # Check origin of local element
        resp2 = client.get(
            "/api/inheritance/gp-origin-child/origin/local"
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["source_graph_id"] == "gp-origin-child"
        assert data2["depth"] == 0

    def test_get_origin_not_found(self, client: TestClient):
        client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "gp-o-parent",
                    "child_id": "gp-o-child",
                    "inheritance_type": "FULL",
                },
            },
        )
        response = client.get(
            "/api/inheritance/gp-o-child/origin/nonexistent"
        )
        assert response.status_code == 404

    def test_list_parents_endpoint(self, client: TestClient):
        payload = {
            "config": {
                "parent_id": "gp-parents-parent",
                "child_id": "gp-parents-child",
                "inheritance_type": "FULL",
            },
        }
        client.post("/api/inheritance/set-parent", json=payload)

        response = client.get("/api/inheritance/gp-parents-child/parents")
        assert response.status_code == 200
        data = response.json()
        assert data["graph_id"] == "gp-parents-child"
        assert data["parent_count"] >= 1
        assert any(p["id"] == "gp-parents-parent" for p in data["parents"])

    def test_list_parents_not_found(self, client: TestClient):
        response = client.get("/api/inheritance/no-such-graph/parents")
        assert response.status_code == 404

    def test_set_parent_circular_detection(self, client: TestClient):
        # Create chain: a -> b -> c
        client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "circ-a",
                    "child_id": "circ-b",
                    "inheritance_type": "FULL",
                },
            },
        )
        client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "circ-b",
                    "child_id": "circ-c",
                    "inheritance_type": "FULL",
                },
            },
        )

        # Try to make 'a' a child of 'c' -> circular
        response = client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "circ-c",
                    "child_id": "circ-a",
                    "inheritance_type": "FULL",
                },
            },
        )
        assert response.status_code == 400
        assert "circular" in response.json()["detail"].lower()

    def test_set_parent_self_parent(self, client: TestClient):
        response = client.post(
            "/api/inheritance/set-parent",
            json={
                "config": {
                    "parent_id": "self",
                    "child_id": "self",
                    "inheritance_type": "FULL",
                },
            },
        )
        assert response.status_code == 400
        assert "own parent" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_id(graph_data: dict[str, Any]) -> str:
    """Extract the ID from a graph dict's metadata."""
    return graph_data.get("metadata", {}).get("id", "")
