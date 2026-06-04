"""Tests for Query Service and Controller.

Tests cover:
1. QueryService selectors (get_nodes_by_kind, get_edges_by_kind, etc.)
2. Entity tree extraction with cycle detection
3. Query API endpoints
4. Edge cases: empty graph, nonexistent node, max depth
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.services.query.query_service import QueryService


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def sample_concept_row():
    return {
        "n": {
            "id": "concept-1",
            "name": "Person",
            "description": "A person entity",
            "graph_id": "mm-1",
            "x_position": 100.0,
            "y_position": 200.0,
            "created_at": None,
            "updated_at": None,
        }
    }


@pytest.fixture
def sample_attribute_row():
    return {
        "n": {
            "id": "attr-1",
            "name": "firstName",
            "description": "First name of the person",
            "type": "string",
            "is_required": True,
            "is_unique": False,
            "graph_id": "mm-1",
            "concept_id": "concept-1",
            "created_at": None,
            "updated_at": None,
        }
    }


@pytest.fixture
def sample_relation_row():
    return {
        "n": {
            "id": "rel-1",
            "name": "has_address",
            "description": "Person has an address",
            "type": "has_part",
            "graph_id": "mm-1",
            "created_at": None,
            "updated_at": None,
        }
    }


def _make_node_result(records: list[dict[str, Any]], key: str = "n"):
    """Build a MockNeo4jResult-like list for a list of node records."""
    return [{key: rec[key]} if key in rec else rec for rec in records]


# ======================================================================
# QueryService Tests
# ======================================================================


class TestSelectorGetNodesByKind:
    """Tests for QueryService.get_nodes_by_kind"""

    def test_get_concepts(self, mock_db, sample_concept_row):
        """Should return concepts when kind='concept'."""
        mock_db.add_result([sample_concept_row])
        service = QueryService(mock_db)
        nodes = service.get_nodes_by_kind("concept")
        assert len(nodes) == 1
        assert nodes[0]["name"] == "Person"
        assert nodes[0]["_kind"] == "concept"

    def test_get_concepts_with_graph_id(self, mock_db):
        """Should filter by graph_id when provided."""
        mock_db.add_result([
            {"n": {"id": "c1", "name": "Person", "graph_id": "mm-1"}},
        ])
        service = QueryService(mock_db)
        nodes = service.get_nodes_by_kind("concept", graph_id="mm-1")
        assert len(nodes) == 1
        # Verify the query contained the graph_id filter
        last_query, last_params = mock_db.executed_queries[-1]
        assert "graph_id" in last_query or "$graph_id" in last_query

    def test_unknown_kind(self, mock_db):
        """Should raise ValueError for unknown node kind."""
        service = QueryService(mock_db)
        with pytest.raises(ValueError, match="Unknown node kind"):
            service.get_nodes_by_kind("unicorn")

    def test_empty_result(self, mock_db):
        """Should return empty list when no nodes match."""
        mock_db.add_result([])
        service = QueryService(mock_db)
        nodes = service.get_nodes_by_kind("attribute")
        assert nodes == []


class TestSelectorGetEdgesByKind:
    """Tests for QueryService.get_edges_by_kind"""

    def _make_edge_row(self, src: str, tgt: str, src_label: str = "A", tgt_label: str = "B"):
        return {
            "source_id": src,
            "source_label": src_label,
            "target_id": tgt,
            "target_label": tgt_label,
            "r": None,
        }

    def test_get_domain_edges(self, mock_db):
        """Should return domain edges."""
        mock_db.add_result([self._make_edge_row("rel-1", "concept-1")])
        service = QueryService(mock_db)
        edges = service.get_edges_by_kind("domain")
        assert len(edges) == 1
        assert edges[0]["type"] == "DOMAIN"
        assert edges[0]["source_id"] == "rel-1"
        assert edges[0]["target_id"] == "concept-1"

    def test_get_single_edge_with_graph_id(self, mock_db):
        """Should scope by graph_id when provided."""
        mock_db.add_result([self._make_edge_row("c1", "c2")])
        service = QueryService(mock_db)
        edges = service.get_edges_by_kind("range", graph_id="mm-1")
        assert len(edges) == 1
        last_query, _ = mock_db.executed_queries[-1]
        assert "graph_id" in last_query

    def test_unknown_kind(self, mock_db):
        """Should raise ValueError for unknown edge kind."""
        service = QueryService(mock_db)
        with pytest.raises(ValueError, match="Unknown edge kind"):
            service.get_edges_by_kind("unknown_edge")

    def test_empty_result(self, mock_db):
        """Should return empty list when no edges match."""
        mock_db.add_result([])
        service = QueryService(mock_db)
        edges = service.get_edges_by_kind("subclass_of")
        assert edges == []


class TestSelectorGetNeighbors:
    """Tests for QueryService.get_neighbors"""

    def test_get_neighbors(self, mock_db):
        """Should return neighboring nodes."""
        # The UNION query returns all results (outgoing + incoming) in one go
        mock_db.add_result([
            {"neighbor": {"id": "n2", "name": "Address"}, "edge_type": "HAS_ATTRIBUTE", "direction": "outgoing"},
            {"neighbor": {"id": "n3", "name": "Owner"}, "edge_type": "SUBCLASS_OF", "direction": "incoming"},
        ])
        service = QueryService(mock_db)
        neighbors = service.get_neighbors("n1")
        assert len(neighbors) == 2

    def test_no_neighbors(self, mock_db):
        """Should return empty list when node has no neighbors."""
        mock_db.add_result([])  # UNION query returns empty
        service = QueryService(mock_db)
        neighbors = service.get_neighbors("lonely-node")
        assert neighbors == []


class TestSelectorGetIncidentEdges:
    """Tests for QueryService.get_incident_edges"""

    def test_get_incident_edges(self, mock_db):
        """Should return incident edges."""
        # The UNION query returns all results in one go
        mock_db.add_result([
            {"source_id": "n1", "source_label": "Person", "target_id": "n2", "target_label": "Address",
             "edge_type": "HAS_ATTRIBUTE", "direction": "outgoing"},
            {"source_id": "n3", "source_label": "Organization", "target_id": "n1", "target_label": "Person",
             "edge_type": "SUBCLASS_OF", "direction": "incoming"},
        ])
        service = QueryService(mock_db)
        edges = service.get_incident_edges("n1")
        assert len(edges) == 2

    def test_no_edges(self, mock_db):
        """Should return empty list when node has no edges."""
        mock_db.add_result([])  # UNION query returns empty
        service = QueryService(mock_db)
        edges = service.get_incident_edges("isolated-node")
        assert edges == []


# ======================================================================
# Entity Tree Tests
# ======================================================================


class TestEntityTree:
    """Tests for QueryService.get_entity_tree"""

    def test_root_not_found(self, mock_db):
        """Should return None when root node does not exist."""
        service = QueryService(mock_db)
        tree = service.get_entity_tree("nonexistent-id")
        assert tree is None

    def test_single_node_no_edges(self, mock_db):
        """Tree for a node with no edges should have empty fields/relations."""
        # _get_node_by_id tries each label; we make Concept match first
        mock_db.add_result([{"n": {"id": "c1", "name": "Solo", "graph_id": "mm-1"}}])
        # get_incident_edges returns empty (UNION query)
        mock_db.add_result([])

        service = QueryService(mock_db)
        tree = service.get_entity_tree("c1")
        assert tree is not None
        assert tree["entity"]["name"] == "Solo"
        assert tree["fields"] == []
        assert tree["relations"] == []

    def test_simple_tree_with_field(self, mock_db):
        """Tree with a concept and an attribute field."""
        # _get_node_by_id for "c1" → Concept label match
        mock_db.add_result([{"n": {"id": "c1", "name": "Person", "graph_id": "mm-1"}}])
        # get_incident_edges for "c1" (UNION: outgoing + incoming)
        mock_db.add_result([
            {"source_id": "c1", "source_label": "Person", "target_id": "a1", "target_label": "name",
             "edge_type": "HAS_ATTRIBUTE", "direction": "outgoing"},
        ])
        # _get_node_by_id for "a1" - will try Attribute label
        mock_db.add_result([{"n": {"id": "a1", "name": "name", "graph_id": "mm-1", "type": "string"}}])
        # get_incident_edges for "a1" (UNION: returns empty)
        mock_db.add_result([])

        service = QueryService(mock_db)
        tree = service.get_entity_tree("c1", max_depth=2)
        assert tree is not None
        assert tree["entity"]["name"] == "Person"
        assert len(tree["fields"]) == 1
        assert tree["fields"][0]["entity"]["name"] == "name"
        assert tree["relations"] == []

    def test_cycle_detection(self, mock_db):
        """Should avoid infinite recursion when graph has cycles."""
        # Root: get_entity_tree("a")
        mock_db.add_result([{"n": {"id": "a", "name": "NodeA", "graph_id": "mm-1"}}])   # _get_node_by_id("a")
        mock_db.add_result([                                                             # get_incident_edges("a")
            {"source_id": "a", "source_label": "NodeA", "target_id": "b", "target_label": "NodeB",
             "edge_type": "SUBCLASS_OF", "direction": "outgoing"},
        ])
        mock_db.add_result([{"n": {"id": "b", "name": "NodeB", "graph_id": "mm-1"}}])   # _get_node_by_id("b") in root
        # Recursive: get_entity_tree("b")
        mock_db.add_result([{"n": {"id": "b", "name": "NodeB", "graph_id": "mm-1"}}])   # _get_node_by_id("b") in recursion
        mock_db.add_result([                                                             # get_incident_edges("b")
            {"source_id": "a", "source_label": "NodeA", "target_id": "b", "target_label": "NodeB",
             "edge_type": "SUBCLASS_OF", "direction": "incoming"},
        ])
        mock_db.add_result([{"n": {"id": "a", "name": "NodeA", "graph_id": "mm-1"}}])   # _get_node_by_id("a") in recursion b

        service = QueryService(mock_db)
        tree = service.get_entity_tree("a", max_depth=5)
        assert tree is not None
        assert tree["entity"]["name"] == "NodeA"
        # b should be in relations, and a should NOT appear inside b's tree (cycle)
        assert len(tree["relations"]) == 1
        rel_b = tree["relations"][0]
        assert rel_b["entity"]["name"] == "NodeB"

    def test_max_depth_limit(self, mock_db):
        """Should stop recursion at max_depth."""
        # Build a chain a → b → c. With max_depth=1, we get a→b but not c.
        # We need to account for all _get_node_by_id and get_incident_edges calls.
        
        def node_row(node_id, name):
            return [{"n": {"id": node_id, "name": name, "graph_id": "mm-1"}}]
        
        def edge_rows(*tuples):
            """Build edge result list from (src_id, src_label, tgt_id, tgt_label, direction) tuples."""
            rows = []
            for src_id, src_label, tgt_id, tgt_label, direction in tuples:
                rows.append({
                    "source_id": src_id, "source_label": src_label,
                    "target_id": tgt_id, "target_label": tgt_label,
                    "edge_type": "SUBCLASS_OF", "direction": direction,
                })
            return rows
        
        # Root "a" (depth 0):
        mock_db.add_result(node_row("a", "NodeA"))  # _get_node_by_id("a")
        mock_db.add_result(edge_rows(("a","NodeA","b","NodeB","outgoing")))  # get_incident_edges("a")
        mock_db.add_result(node_row("b", "NodeB"))  # _get_node_by_id("b") in root context
        
        # Recursive "b" (depth 1):
        mock_db.add_result(node_row("b", "NodeB"))  # _get_node_by_id("b") recursive
        mock_db.add_result(edge_rows(               # get_incident_edges("b")
            ("b","NodeB","c","NodeC","outgoing"),
            ("a","NodeA","b","NodeB","incoming"),
        ))
        mock_db.add_result(node_row("c", "NodeC"))  # _get_node_by_id("c") - depth 1+1 > max_depth 1, no recursion
        mock_db.add_result(node_row("a", "NodeA"))  # _get_node_by_id("a") - already visited

        service = QueryService(mock_db)
        
        tree = service.get_entity_tree("a", max_depth=1)
        assert tree is not None
        assert tree["entity"]["name"] == "NodeA"
        # With max_depth=1: a→b is included, but c should NOT be recursed into

    def test_no_entity_tree_for_cycle_at_root(self, mock_db):
        """Self-loop should be handled gracefully."""
        mock_db.add_result([{"n": {"id": "self", "name": "SelfLoop", "graph_id": "mm-1"}}])
        # get_incident_edges: outgoing self-loop
        mock_db.add_result([
            {"source_id": "self", "source_label": "SelfLoop", "target_id": "self", "target_label": "SelfLoop",
             "edge_type": "SUBCLASS_OF", "direction": "outgoing"},
        ])

        service = QueryService(mock_db)
        tree = service.get_entity_tree("self", max_depth=5)
        assert tree is not None
        assert tree["entity"]["name"] == "SelfLoop"
        # Self-loop should not cause infinite recursion
        assert len(tree["relations"]) == 0  # self-reference skipped via _visited


# ======================================================================
# API Endpoint Tests
# ======================================================================


class TestQueryAPI:
    """Tests for query API endpoints using TestClient."""

    def test_get_nodes_by_kind_endpoint(self, client: TestClient, mock_db):
        """GET /api/query/nodes/{kind} should return nodes."""
        mock_db.add_result([{"n": {"id": "c1", "name": "Person", "graph_id": "mm-1"}}])
        resp = client.get("/api/query/nodes/concept")
        assert resp.status_code == 200
        data = resp.json()
        assert data["kind"] == "concept"
        assert data["count"] == 1
        assert len(data["data"]) == 1

    def test_get_nodes_by_kind_with_graph_id(self, client: TestClient, mock_db):
        """GET /api/query/nodes/{kind}?graph_id= should filter."""
        mock_db.add_result([{"n": {"id": "c1", "name": "Person", "graph_id": "mm-1"}}])
        resp = client.get("/api/query/nodes/concept?graph_id=mm-1")
        assert resp.status_code == 200

    def test_get_nodes_unknown_kind(self, client: TestClient, mock_db):
        """Should return 400 for unknown kind."""
        resp = client.get("/api/query/nodes/unicorn")
        assert resp.status_code == 400

    def test_get_edges_by_kind_endpoint(self, client: TestClient, mock_db):
        """GET /api/query/edges/{kind} should return edges."""
        mock_db.add_result([
            {"source_id": "r1", "source_label": "has_address", "target_id": "c1", "target_label": "Address",
             "direction": "outgoing", "edge_type": "RANGE", "r": None},
        ])
        resp = client.get("/api/query/edges/range")
        assert resp.status_code == 200
        data = resp.json()
        assert data["kind"] == "range"

    def test_get_edges_unknown_kind(self, client: TestClient, mock_db):
        """Should return 400 for unknown edge kind."""
        resp = client.get("/api/query/edges/invalid")
        assert resp.status_code == 400

    def test_get_neighbors_endpoint(self, client: TestClient, mock_db):
        """GET /api/query/node/{id}/neighbors should return neighbors."""
        mock_db.add_result([
            {"neighbor": {"id": "n2", "name": "Address"}, "edge_type": "HAS_ATTRIBUTE", "direction": "outgoing"},
        ])
        resp = client.get("/api/query/node/n1/neighbors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["node_id"] == "n1"

    def test_get_incident_edges_endpoint(self, client: TestClient, mock_db):
        """GET /api/query/node/{id}/edges should return incident edges."""
        mock_db.add_result([
            {"source_id": "n1", "source_label": "Person", "target_id": "n2", "target_label": "Address",
             "edge_type": "HAS_ATTRIBUTE", "direction": "outgoing"},
        ])
        resp = client.get("/api/query/node/n1/edges")
        assert resp.status_code == 200
        data = resp.json()
        assert data["node_id"] == "n1"

    def test_get_entity_tree_endpoint(self, client: TestClient, mock_db):
        """GET /api/query/tree/{id} should return entity tree."""
        # _get_node_by_id
        mock_db.add_result([{"n": {"id": "c1", "name": "Person", "graph_id": "mm-1"}}])
        # get_incident_edges (UNION query)
        mock_db.add_result([])

        resp = client.get("/api/query/tree/c1?max_depth=3")
        assert resp.status_code == 200
        data = resp.json()
        assert data["entity"]["name"] == "Person"

    def test_get_entity_tree_not_found(self, client: TestClient, mock_db):
        """Should return 404 when root node not found."""
        resp = client.get("/api/query/tree/nonexistent")
        assert resp.status_code == 404

    def test_get_entity_tree_with_invalid_depth(self, client: TestClient, mock_db):
        """Should validate max_depth parameter."""
        resp = client.get("/api/query/tree/c1?max_depth=0")
        assert resp.status_code == 422  # Validation error

    def test_find_pattern_endpoint(self, client: TestClient, mock_db):
        """POST /api/query/pattern should return matches."""
        mock_db.add_result([
            {"a": {"id": "c1", "name": "Car", "graph_id": "mm-1"},
             "b": {"id": "c2", "name": "Vehicle", "graph_id": "mm-1"}},
        ])
        pattern = [
            {"alias": "a", "kind": "concept"},
            {"alias": "b", "kind": "concept",
             "edges": [{"to": "a", "type": "SUBCLASS_OF"}]},
        ]
        resp = client.post("/api/query/pattern", json=pattern)
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1


# ======================================================================
# Edge Case Tests
# ======================================================================


class TestEdgeCases:
    """Edge case tests for the query system."""

    def test_empty_graph(self, mock_db):
        """Querying an empty graph should return empty results."""
        mock_db.add_result([])  # Empty result for nodes
        service = QueryService(mock_db)
        nodes = service.get_nodes_by_kind("concept")
        assert nodes == []

    def test_node_with_many_edges(self, mock_db):
        """Should handle a node with many incident edges."""
        mock_db.add_result([{"n": {"id": "hub", "name": "Hub", "graph_id": "mm-1"}}])
        # 10 outgoing edges (UNION query returns all in one result)
        outgoing = [
            {"source_id": "hub", "source_label": "Hub",
             "target_id": f"n{i}", "target_label": f"Node{i}",
             "edge_type": "HAS_ATTRIBUTE", "direction": "outgoing"}
            for i in range(10)
        ]
        mock_db.add_result(outgoing)
        for i in range(10):
            mock_db.add_result([{"n": {"id": f"n{i}", "name": f"Node{i}", "graph_id": "mm-1"}}])
            mock_db.add_result([])  # get_incident_edges for each child

        service = QueryService(mock_db)
        tree = service.get_entity_tree("hub", max_depth=2)
        assert tree is not None
        assert len(tree["fields"]) == 10  # attributes are fields

    def test_get_neighbors_deduplication(self, mock_db):
        """get_neighbors should not return the same node twice."""
        # Same neighbor connected via two different edge types
        # UNION query returns all in one result
        mock_db.add_result([
            {"neighbor": {"id": "n2", "name": "Same"}, "edge_type": "SUBCLASS_OF", "direction": "outgoing"},
            {"neighbor": {"id": "n2", "name": "Same"}, "edge_type": "HAS_ATTRIBUTE", "direction": "incoming"},
        ])
        service = QueryService(mock_db)
        neighbors = service.get_neighbors("n1")
        # Should only appear once (deduplicated by ID)
        assert len(neighbors) == 1
