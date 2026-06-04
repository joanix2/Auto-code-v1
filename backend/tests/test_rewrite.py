"""Tests for the Rewrite Engine (rules, pattern matcher, engine, API).

Tests cover:
1. RewriteRule — creation, condition/action, to_dict, immutability.
2. PatternMatcher — basic matching, wildcards, conditions, edge cases.
3. RewriteEngine — single rule, all rules, fixpoint, error handling.
4. Default rules — normalize_names, remove_orphan_edges, deduplicate_nodes,
   infer_missing_labels.
5. API endpoints — /api/rewrite/rules, /api/rewrite/apply,
   /api/rewrite/fixpoint, /api/rewrite/match.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.services.rewrite import DEFAULT_RULES, RewriteEngine, RewriteRule, match_pattern
from src.services.rewrite.default_rules import (
    DEDUPLICATE_NODES,
    INFER_MISSING_LABELS,
    NORMALIZE_NAMES,
    REMOVE_ORPHAN_EDGES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_graph():
    """A minimal valid IR graph."""
    return {
        "metadata": {"id": "g1", "name": "Test", "version": "1.0.0"},
        "nodes": [
            {"id": "n1", "name": "Alice", "type": "concept"},
            {"id": "n2", "name": "Bob", "type": "concept"},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2", "type": "KNOWS"},
        ],
    }


@pytest.fixture
def graph_with_whitespace():
    """Graph with leading/trailing whitespace in names."""
    return {
        "metadata": {"id": "g2", "name": "  Dirty  ", "version": "1.0.0"},
        "nodes": [
            {"id": "n1", "name": "  Alice  ", "type": "concept"},
            {"id": "n2", "name": " Bob", "type": "concept"},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2", "type": "KNOWS"},
        ],
    }


@pytest.fixture
def graph_with_orphans():
    """Graph where an edge references a non-existent node."""
    return {
        "metadata": {"id": "g3", "name": "Orphans", "version": "1.0.0"},
        "nodes": [
            {"id": "n1", "name": "Exists", "type": "concept"},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "missing", "type": "KNOWS"},
            {"id": "e2", "source": "n1", "target": "n1", "type": "SELF"},
        ],
    }


@pytest.fixture
def graph_with_duplicates():
    """Graph with duplicate nodes (same name + type)."""
    return {
        "metadata": {"id": "g4", "name": "Dupes", "version": "1.0.0"},
        "nodes": [
            {"id": "n1", "name": "Alice", "type": "concept"},
            {"id": "n2", "name": "Alice", "type": "concept"},
            {"id": "n3", "name": "Bob", "type": "concept"},
        ],
        "edges": [
            {"id": "e1", "source": "n2", "target": "n3", "type": "KNOWS"},
            {"id": "e2", "source": "n3", "target": "n1", "type": "KNOWS"},
        ],
    }


@pytest.fixture
def graph_with_missing_labels():
    """Graph where some nodes have no label."""
    return {
        "metadata": {"id": "g5", "name": "Labels", "version": "1.0.0"},
        "nodes": [
            {"id": "n1", "name": "Alice", "type": "concept"},
            {"id": "n2", "name": "Bob", "type": "concept", "label": "Bobby"},
            {"id": "n3", "name": "Charlie", "type": "concept", "label": ""},
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2", "type": "KNOWS"},
        ],
    }


# ===================================================================
# RewriteRule Tests
# ===================================================================


class TestRewriteRule:
    """Tests for the RewriteRule data class."""

    def test_create_rule(self):
        rule = RewriteRule(
            name="test_rule",
            description="A test rule",
            condition=lambda g: True,
            action=lambda g: g,
        )
        assert rule.name == "test_rule"
        assert rule.enabled is True
        assert rule.priority == 100

    def test_rule_condition_true_fires_action(self):
        rule = RewriteRule(
            name="add_tag",
            description="Add a tag",
            condition=lambda g: True,
            action=lambda g: {**g, "tagged": True},
        )
        result = rule({"nodes": []})
        assert result is not None
        assert result["tagged"] is True

    def test_rule_condition_false_returns_none(self):
        rule = RewriteRule(
            name="never",
            description="Never fires",
            condition=lambda g: False,
            action=lambda g: g,
        )
        result = rule({"nodes": []})
        assert result is None

    def test_disabled_rule_returns_none(self):
        rule = RewriteRule(
            name="disabled",
            description="Disabled rule",
            condition=lambda g: True,
            action=lambda g: g,
            enabled=False,
        )
        result = rule({"nodes": []})
        assert result is None

    def test_to_dict(self):
        rule = RewriteRule(
            name="r",
            description="d",
            condition=lambda g: True,
            action=lambda g: g,
            priority=50,
        )
        d = rule.to_dict()
        assert d["name"] == "r"
        assert d["description"] == "d"
        assert d["priority"] == 50
        assert d["enabled"] is True
        assert "condition" not in d  # callable not serialised

    def test_priority_ordering(self):
        low = RewriteRule(
            name="low", description="", condition=lambda g: True,
            action=lambda g: g, priority=10,
        )
        high = RewriteRule(
            name="high", description="", condition=lambda g: True,
            action=lambda g: g, priority=100,
        )
        engine = RewriteEngine()
        engine.register_rules([high, low])
        names = [r["name"] for r in engine.list_rules()]
        assert names == ["low", "high"]  # sorted by priority


# ===================================================================
# PatternMatcher Tests
# ===================================================================


class TestPatternMatcher:
    """Tests for the pattern matching module."""

    def test_match_basic(self, simple_graph):
        pattern = {
            "nodes": {
                "a": {"type": "concept"},
                "b": {"type": "concept"},
            },
            "edges": [
                {"source": "a", "target": "b", "type": "KNOWS"},
            ],
        }
        matches = match_pattern(simple_graph, pattern)
        assert len(matches) == 1
        assert matches[0]["a"]["id"] == "n1"
        assert matches[0]["b"]["id"] == "n2"

    def test_match_with_wildcard(self, simple_graph):
        """None in node spec means wildcard (match any value)."""
        pattern = {
            "nodes": {
                "x": {"name": None},  # any name
            },
        }
        matches = match_pattern(simple_graph, pattern)
        assert len(matches) == 2  # both nodes match

    def test_match_with_wildcard_edge_type(self, simple_graph):
        pattern = {
            "nodes": {
                "a": {"type": "concept"},
                "b": {"type": "concept"},
            },
            "edges": [
                {"source": "a", "target": "b", "type": "*"},
            ],
        }
        matches = match_pattern(simple_graph, pattern)
        assert len(matches) == 1

    def test_no_match(self, simple_graph):
        pattern = {
            "nodes": {
                "x": {"type": "attribute"},
            },
        }
        matches = match_pattern(simple_graph, pattern)
        assert len(matches) == 0

    def test_match_with_condition(self, simple_graph):
        pattern = {
            "nodes": {
                "a": {"type": "concept"},
            },
            "conditions": [
                {"field": "a.name", "op": "startswith", "value": "A"},
            ],
        }
        matches = match_pattern(simple_graph, pattern)
        assert len(matches) == 1
        assert matches[0]["a"]["name"] == "Alice"

    def test_match_with_condition_not_satisfied(self, simple_graph):
        pattern = {
            "nodes": {
                "a": {"type": "concept"},
            },
            "conditions": [
                {"field": "a.name", "op": "eq", "value": "Nobody"},
            ],
        }
        matches = match_pattern(simple_graph, pattern)
        assert len(matches) == 0

    def test_empty_pattern_returns_empty(self, simple_graph):
        assert match_pattern(simple_graph, {}) == []
        assert match_pattern(simple_graph, {"nodes": {}}) == []

    def test_empty_graph_returns_empty(self):
        empty = {"metadata": {}, "nodes": [], "edges": []}
        pattern = {
            "nodes": {"a": {"type": "concept"}},
        }
        assert match_pattern(empty, pattern) == []


# ===================================================================
# RewriteEngine Tests
# ===================================================================


class TestRewriteEngine:
    """Tests for the RewriteEngine."""

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def test_register_rule(self):
        engine = RewriteEngine()
        rule = RewriteRule(
            name="r1", description="", condition=lambda g: True,
            action=lambda g: g,
        )
        engine.register_rule(rule)
        assert len(engine.list_rules()) == 1

    def test_register_duplicate_raises(self):
        engine = RewriteEngine()
        rule = RewriteRule(
            name="r1", description="", condition=lambda g: True,
            action=lambda g: g,
        )
        engine.register_rule(rule)
        with pytest.raises(ValueError, match="already registered"):
            engine.register_rule(rule)

    def test_register_rules_bulk(self):
        engine = RewriteEngine()
        rules = [
            RewriteRule(name=f"r{i}", description="", condition=lambda g: True,
                        action=lambda g: g)
            for i in range(3)
        ]
        engine.register_rules(rules)
        assert len(engine.list_rules()) == 3

    def test_unregister_rule(self):
        engine = RewriteEngine()
        rule = RewriteRule(name="r1", description="", condition=lambda g: True,
                           action=lambda g: g)
        engine.register_rule(rule)
        engine.unregister_rule("r1")
        assert len(engine.list_rules()) == 0

    def test_get_rule(self):
        engine = RewriteEngine()
        rule = RewriteRule(name="r1", description="d", condition=lambda g: True,
                           action=lambda g: g)
        engine.register_rule(rule)
        assert engine.get_rule("r1") is rule
        assert engine.get_rule("nonexistent") is None

    # ------------------------------------------------------------------
    # apply_rule
    # ------------------------------------------------------------------

    def test_apply_rule_fires(self):
        engine = RewriteEngine()
        rule = RewriteRule(
            name="add_x",
            description="",
            condition=lambda g: True,
            action=lambda g: {**g, "x": 1},
        )
        engine.register_rule(rule)
        result = engine.apply_rule("add_x", {"nodes": []})
        assert result.success is True
        assert "add_x" in result.applied_rules
        assert result.modified_graph.get("x") == 1

    def test_apply_rule_no_fire(self):
        engine = RewriteEngine()
        rule = RewriteRule(
            name="never",
            description="",
            condition=lambda g: False,
            action=lambda g: g,
        )
        engine.register_rule(rule)
        result = engine.apply_rule("never", {"nodes": []})
        assert result.success is True
        assert result.applied_rules == []

    def test_apply_rule_not_found(self):
        engine = RewriteEngine()
        result = engine.apply_rule("missing", {"nodes": []})
        assert result.success is False
        assert "not found" in result.errors[0]

    def test_apply_rule_exception(self):
        def broken_action(g):
            raise RuntimeError("oops")

        engine = RewriteEngine()
        rule = RewriteRule(name="broken", description="", condition=lambda g: True,
                           action=broken_action)
        engine.register_rule(rule)
        result = engine.apply_rule("broken", {"nodes": []})
        assert result.success is False
        assert "broken" in result.errors[0]

    # ------------------------------------------------------------------
    # apply_all
    # ------------------------------------------------------------------

    def test_apply_all_runs_all(self):
        engine = RewriteEngine()
        engine.register_rules(DEFAULT_RULES)
        graph = {
            "metadata": {"id": "x", "name": "  test  ", "version": "1"},
            "nodes": [
                {"id": "n1", "name": "  A  ", "type": "concept"},
                {"id": "n2", "name": "B", "type": "concept"},
                {"id": "n3", "name": "B", "type": "concept"},  # duplicate
            ],
            "edges": [
                {"id": "e1", "source": "n1", "target": "n2", "type": "X"},
                {"id": "e2", "source": "n1", "target": "missing", "type": "Y"},
            ],
        }
        result = engine.apply_all(graph)
        assert result.success is True
        assert len(result.applied_rules) >= 1  # at least one rule fired

    def test_apply_all_empty_rules(self, simple_graph):
        engine = RewriteEngine()
        result = engine.apply_all(simple_graph)
        assert result.success is True
        assert result.applied_rules == []
        assert result.modified_graph == simple_graph

    # ------------------------------------------------------------------
    # apply_fixpoint
    # ------------------------------------------------------------------

    def test_fixpoint_converges(self, graph_with_whitespace):
        engine = RewriteEngine()
        engine.register_rule(NORMALIZE_NAMES)
        result = engine.apply_fixpoint(graph_with_whitespace, max_iterations=5)
        assert result.success is True
        assert len(result.applied_rules) >= 1
        # After fixpoint, names should be clean
        for node in result.modified_graph.get("nodes", []):
            name = node.get("name", "")
            assert name == name.strip()

    def test_fixpoint_max_iterations(self):
        """A rule that always fires will hit the iteration limit."""
        engine = RewriteEngine()
        counter = 0

        def always_fires(g):
            nonlocal counter
            counter += 1
            return {**g, "count": counter}

        engine.register_rule(
            RewriteRule(
                name="always",
                description="",
                condition=lambda g: True,
                action=always_fires,
                priority=1,
            )
        )
        result = engine.apply_fixpoint({"nodes": []}, max_iterations=3)
        assert result.success is False  # did not converge
        assert result.iteration_count == 3

    def test_fixpoint_no_rules(self, simple_graph):
        engine = RewriteEngine()
        result = engine.apply_fixpoint(simple_graph, max_iterations=5)
        assert result.success is True
        assert result.applied_rules == []


# ===================================================================
# Default Rules Tests
# ===================================================================


class TestDefaultRules:
    """Tests for each default rewrite rule."""

    # ------------------------------------------------------------------
    # normalize_names
    # ------------------------------------------------------------------

    def test_normalize_names_condition_true(self, graph_with_whitespace):
        assert NORMALIZE_NAMES.condition(graph_with_whitespace) is True

    def test_normalize_names_condition_false(self, simple_graph):
        assert NORMALIZE_NAMES.condition(simple_graph) is False

    def test_normalize_names_action(self, graph_with_whitespace):
        result = NORMALIZE_NAMES.action(graph_with_whitespace)
        for node in result.get("nodes", []):
            name = node.get("name", "")
            assert name == name.strip(), f"Name '{name}' not stripped"

    # ------------------------------------------------------------------
    # remove_orphan_edges
    # ------------------------------------------------------------------

    def test_orphan_condition_true(self, graph_with_orphans):
        assert REMOVE_ORPHAN_EDGES.condition(graph_with_orphans) is True

    def test_orphan_condition_false(self, simple_graph):
        assert REMOVE_ORPHAN_EDGES.condition(simple_graph) is False

    def test_orphan_action_removes_bad_edge(self, graph_with_orphans):
        result = REMOVE_ORPHAN_EDGES.action(graph_with_orphans)
        edge_ids = [e["id"] for e in result.get("edges", [])]
        assert "e1" not in edge_ids  # orphan removed
        assert "e2" in edge_ids  # self-loop kept (valid)

    # ------------------------------------------------------------------
    # deduplicate_nodes
    # ------------------------------------------------------------------

    def test_deduplicate_condition_true(self, graph_with_duplicates):
        assert DEDUPLICATE_NODES.condition(graph_with_duplicates) is True

    def test_deduplicate_condition_false(self, simple_graph):
        assert DEDUPLICATE_NODES.condition(simple_graph) is False

    def test_deduplicate_action_merges_nodes(self, graph_with_duplicates):
        result = DEDUPLICATE_NODES.action(graph_with_duplicates)
        assert len(result["nodes"]) == 2  # Alice + Bob (dupe Alice removed)
        names = {n["name"] for n in result["nodes"]}
        assert names == {"Alice", "Bob"}

    def test_deduplicate_action_rewires_edges(self, graph_with_duplicates):
        result = DEDUPLICATE_NODES.action(graph_with_duplicates)
        # Edges that pointed to n2 should now point to n1
        for edge in result["edges"]:
            assert edge["source"] != "n2"  # n2 should be gone
            assert edge["target"] != "n2"

    # ------------------------------------------------------------------
    # infer_missing_labels
    # ------------------------------------------------------------------

    def test_infer_labels_condition_true(self, graph_with_missing_labels):
        assert INFER_MISSING_LABELS.condition(graph_with_missing_labels) is True

    def test_infer_labels_condition_false(self):
        """All nodes already have a non-empty label — condition should be False."""
        graph = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [
                {"id": "n1", "name": "Alice", "type": "concept", "label": "Alice"},
                {"id": "n2", "name": "Bob", "type": "concept", "label": "Bob"},
            ],
            "edges": [],
        }
        assert INFER_MISSING_LABELS.condition(graph) is False

    def test_infer_labels_action(self, graph_with_missing_labels):
        result = INFER_MISSING_LABELS.action(graph_with_missing_labels)
        n1 = next(n for n in result["nodes"] if n["id"] == "n1")
        n3 = next(n for n in result["nodes"] if n["id"] == "n3")
        assert n1.get("label") == "Alice"
        assert n3.get("label") == "Charlie"
        # n2 already had a label — should not change
        n2 = next(n for n in result["nodes"] if n["id"] == "n2")
        assert n2.get("label") == "Bobby"

    def test_infer_labels_on_edges_without_name(self):
        """Edges without a name/label should be left as-is."""
        graph = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "n1", "name": "A", "type": "concept"}],
            "edges": [{"id": "e1", "source": "n1", "target": "n1", "type": "SELF"}],
        }
        result = INFER_MISSING_LABELS.action(graph)
        # Edge has no name, so no label inferred
        edge = result["edges"][0]
        assert edge.get("label", "") == ""


# ===================================================================
# API Endpoint Tests
# ===================================================================


class TestRewriteAPI:
    """Tests for the /api/rewrite endpoints."""

    def test_list_rules(self, client: TestClient):
        response = client.get("/api/rewrite/rules")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "rules" in data
        assert data["count"] == len(DEFAULT_RULES)

    def test_apply_rules_all(self, client: TestClient, graph_with_whitespace):
        response = client.post("/api/rewrite/apply", json=graph_with_whitespace)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "graph" in data
        # Names should be cleaned
        for node in data["graph"].get("nodes", []):
            name = node.get("name", "")
            assert name == name.strip()

    def test_apply_single_rule(self, client: TestClient, simple_graph):
        response = client.post(
            "/api/rewrite/apply?rule_name=normalize_names",
            json=simple_graph,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_apply_single_rule_not_found(self, client: TestClient, simple_graph):
        response = client.post(
            "/api/rewrite/apply?rule_name=nonexistent",
            json=simple_graph,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "not found" in str(data["errors"])

    def test_fixpoint(self, client: TestClient, graph_with_whitespace):
        response = client.post("/api/rewrite/fixpoint", json=graph_with_whitespace)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "graph" in data

    def test_fixpoint_with_custom_max_iterations(self, client: TestClient, simple_graph):
        response = client.post(
            "/api/rewrite/fixpoint?max_iterations=5",
            json=simple_graph,
        )
        assert response.status_code == 200

    def test_match_pattern(self, client: TestClient, simple_graph):
        pattern = {
            "nodes": {
                "a": {"type": "concept"},
            },
        }
        response = client.post(
            "/api/rewrite/match",
            json={"graph_data": simple_graph, "pattern": pattern},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["matches"]) == 2

    def test_match_pattern_no_result(self, client: TestClient, simple_graph):
        pattern = {
            "nodes": {
                "x": {"type": "attribute"},
            },
        }
        response = client.post(
            "/api/rewrite/match",
            json={"graph_data": simple_graph, "pattern": pattern},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0


# ===================================================================
# Edge Cases
# ===================================================================


class TestRewriteEdgeCases:
    """Edge-case tests for the rewrite engine."""

    def test_empty_graph(self):
        engine = RewriteEngine()
        engine.register_rules(DEFAULT_RULES)
        empty = {"metadata": {"id": "e", "name": "", "version": "1"}, "nodes": [], "edges": []}
        result = engine.apply_fixpoint(empty)
        assert result.success is True

    def test_no_rules_registered(self, simple_graph):
        engine = RewriteEngine()
        result = engine.apply_all(simple_graph)
        assert result.success is True
        assert result.modified_graph == simple_graph

    def test_action_does_not_mutate_input(self):
        """Actions should not modify the original graph dict."""
        engine = RewriteEngine()
        rule = RewriteRule(
            name="modifier",
            description="",
            condition=lambda g: True,
            action=lambda g: {**g, "modified": True},
        )
        engine.register_rule(rule)
        original = {"nodes": [{"id": "n1", "name": "test", "type": "concept"}]}
        original_copy = copy.deepcopy(original)
        result = engine.apply_rule("modifier", original)
        assert original == original_copy  # should be unchanged

    def test_fixpoint_deduplicate_and_normalize(self):
        """Integration: combine multiple default rules."""
        engine = RewriteEngine()
        engine.register_rules([NORMALIZE_NAMES, DEDUPLICATE_NODES, REMOVE_ORPHAN_EDGES])

        graph = {
            "metadata": {"id": "x", "name": "test", "version": "1"},
            "nodes": [
                {"id": "n1", "name": "  Alice  ", "type": "concept"},
                {"id": "n2", "name": "  Alice  ", "type": "concept"},  # dupe after normalize
                {"id": "n3", "name": "Bob", "type": "concept"},
            ],
            "edges": [
                {"id": "e1", "source": "n2", "target": "n3", "type": "KNOWS"},
            ],
        }
        result = engine.apply_fixpoint(graph)
        assert result.success is True
        assert len(result.modified_graph["nodes"]) <= 2  # should dedupe
        # n2 edge should be rewired to n1
        for edge in result.modified_graph["edges"]:
            assert edge["source"] in {"n1", "n3"}
