"""Tests for the Validation System (structural, business, API).

Tests cover:
1. Structural validation — unique IDs, edge references, allowed types,
   required fields.
2. Business rules — cardinalities, forbidden cycles, domain-specific rules.
3. ValidationReport — grouping, summary, human-readable output.
4. API endpoints — /api/validate/graph and /api/validate/{metamodel_id}.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.services.validation import (
    Severity,
    ValidationError,
    ValidationReport,
    clear_domain_rules,
    register_domain_rule,
    validate_graph,
)
from src.services.validation.business_validator import (
    detect_forbidden_cycles,
    validate_cardinalities,
)
from src.services.validation.structural_validator import (
    run_structural_validators,
    validate_allowed_types,
    validate_edge_references,
    validate_unique_ids,
)
from src.services.validation.validation_report import Severity as Sev

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def valid_graph():
    """A structurally valid IR graph."""
    return {
        "metadata": {
            "id": "graph-1",
            "name": "Test Graph",
            "version": "1.0.0",
            "status": "draft",
            "owner_id": "user-1",
            "allowed_node_types": [
                {
                    "name": "concept",
                    "label": "Concept",
                    "labelPlural": "Concepts",
                    "gender": "m",
                    "article": "le",
                },
                {
                    "name": "attribute",
                    "label": "Attribut",
                    "labelPlural": "Attributs",
                    "gender": "m",
                    "article": "l'",
                },
            ],
            "allowed_edge_types": [
                {
                    "name": "HAS_ATTRIBUTE",
                    "sourceNodeTypes": ["concept"],
                    "targetNodeTypes": ["attribute"],
                    "directed": True,
                },
                {
                    "name": "SUBCLASS_OF",
                    "sourceNodeTypes": ["concept"],
                    "targetNodeTypes": ["concept"],
                    "directed": True,
                },
            ],
        },
        "nodes": [
            {"id": "c1", "name": "Vehicle", "type": "concept"},
            {"id": "c2", "name": "Car", "type": "concept"},
            {"id": "a1", "name": "speed", "type": "attribute"},
        ],
        "edges": [
            {
                "id": "e1",
                "source": "c2",
                "target": "c1",
                "type": "SUBCLASS_OF",
            },
            {
                "id": "e2",
                "source": "c2",
                "target": "a1",
                "type": "HAS_ATTRIBUTE",
            },
        ],
        "edgeConstraints": [],
    }


@pytest.fixture
def duplicate_id_graph():
    """Graph with duplicate IDs across nodes and edges."""
    return {
        "metadata": {"id": "g1", "name": "Duplicates", "version": "1.0.0"},
        "nodes": [
            {"id": "dup", "name": "Node A", "type": "concept"},
            {"id": "dup", "name": "Node B", "type": "concept"},
        ],
        "edges": [
            {"id": "dup", "source": "c1", "target": "c2", "type": "SUBCLASS_OF"},
        ],
    }


@pytest.fixture
def bad_ref_graph():
    """Graph with edge references to non-existent nodes."""
    return {
        "metadata": {"id": "g2", "name": "Bad Refs", "version": "1.0.0"},
        "nodes": [{"id": "n1", "name": "Only Node", "type": "concept"}],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "missing-node",
                "type": "SUBCLASS_OF",
            },
        ],
    }


@pytest.fixture
def invalid_type_graph():
    """Graph with types not in allowed lists."""
    return {
        "metadata": {
            "id": "g3",
            "name": "Bad Types",
            "version": "1.0.0",
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
            {"id": "n1", "name": "Good", "type": "concept"},
            {"id": "n2", "name": "Bad", "type": "unknown_type"},
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "type": "UNKNOWN_EDGE",
            },
        ],
    }


@pytest.fixture
def cyclic_graph():
    """Graph with a SUBCLASS_OF cycle: c1 → c2 → c3 → c1."""
    return {
        "metadata": {"id": "g4", "name": "Cycle", "version": "1.0.0"},
        "nodes": [
            {"id": "c1", "name": "A", "type": "concept"},
            {"id": "c2", "name": "B", "type": "concept"},
            {"id": "c3", "name": "C", "type": "concept"},
        ],
        "edges": [
            {"id": "e1", "source": "c1", "target": "c2", "type": "SUBCLASS_OF"},
            {"id": "e2", "source": "c2", "target": "c3", "type": "SUBCLASS_OF"},
            {"id": "e3", "source": "c3", "target": "c1", "type": "SUBCLASS_OF"},
        ],
    }


# ---------------------------------------------------------------------------
# ValidationReport Tests
# ---------------------------------------------------------------------------


class TestValidationReport:
    """Tests for the ValidationReport data structure."""

    def test_empty_report_is_valid(self):
        report = ValidationReport()
        assert report.is_valid is True
        assert report.has_warnings is False
        assert report.summary()["valid"] is True

    def test_add_error(self):
        report = ValidationReport()
        err = ValidationError(
            code="TEST", message="Test error", severity=Severity.ERROR, location="n1"
        )
        report.add_error(err)
        assert len(report.errors) == 1
        assert report.is_valid is False

    def test_add_warning_is_not_blocking(self):
        report = ValidationReport()
        report.add_error(
            ValidationError(
                code="WARN", message="Warning", severity=Severity.WARNING
            )
        )
        assert report.is_valid is True
        assert report.has_warnings is True

    def test_group_by_severity(self):
        report = ValidationReport()
        report.add_error(
            ValidationError(code="E1", message="Err", severity=Severity.ERROR)
        )
        report.add_error(
            ValidationError(code="W1", message="Warn", severity=Severity.WARNING)
        )
        report.add_error(
            ValidationError(code="I1", message="Info", severity=Severity.INFO)
        )
        groups = report.group_by_severity()
        assert len(groups["error"]) == 1
        assert len(groups["warning"]) == 1
        assert len(groups["info"]) == 1

    def test_human_readable(self):
        report = ValidationReport()
        report.add_error(
            ValidationError(
                code="TEST",
                message="Something went wrong",
                location="n1",
                suggestion="Fix it",
            )
        )
        text = report.human_readable()
        assert "Something went wrong" in text
        assert "Fix it" in text

    def test_merge(self):
        r1 = ValidationReport()
        r1.add_error(ValidationError(code="A", message="A"))
        r2 = ValidationReport()
        r2.add_error(ValidationError(code="B", message="B"))
        r1.merge(r2)
        assert len(r1.errors) == 2

    def test_to_dict(self):
        report = ValidationReport()
        report.add_error(
            ValidationError(
                code="TEST", message="x", severity=Severity.ERROR, location="n1"
            )
        )
        d = report.to_dict()
        assert "summary" in d
        assert "errors" in d
        assert d["errors"][0]["code"] == "TEST"

    def test_errors_by_code(self):
        report = ValidationReport()
        report.add_error(ValidationError(code="ABC", message="1"))
        report.add_error(ValidationError(code="XYZ", message="2"))
        report.add_error(ValidationError(code="ABC", message="3"))
        assert len(report.errors_by_code("ABC")) == 2

    def test_errors_at_location(self):
        report = ValidationReport()
        report.add_error(
            ValidationError(code="A", message="1", location="n1")
        )
        report.add_error(
            ValidationError(code="B", message="2", location="n2")
        )
        report.add_error(
            ValidationError(code="C", message="3", location="n1")
        )
        assert len(report.errors_at_location("n1")) == 2

    def test_frozen_error(self):
        """ValidationError dataclass should be frozen (immutable)."""
        err = ValidationError(code="X", message="Y")
        with pytest.raises(AttributeError):
            err.code = "Z"  # type: ignore[misc]

    def test_error_to_dict(self):
        err = ValidationError(
            code="MY_CODE",
            message="My message",
            severity=Severity.ERROR,
            location="n1",
            suggestion="Do something",
        )
        d = err.to_dict()
        assert d["code"] == "MY_CODE"
        assert d["severity"] == "error"


# ---------------------------------------------------------------------------
# Structural Validator Tests
# ---------------------------------------------------------------------------


class TestStructuralValidator:
    """Tests for structural validation rules."""

    def test_valid_graph_passes(self, valid_graph):
        report = run_structural_validators(valid_graph)
        assert report.is_valid, f"Expected no errors, got: {report.errors}"

    def test_duplicate_id_in_nodes(self, duplicate_id_graph):
        report = validate_unique_ids(duplicate_id_graph)
        assert len(report.errors) >= 1
        assert any(e.code == "DUPLICATE_ID" for e in report.errors)

    def test_duplicate_id_across_nodes_and_edges(self, duplicate_id_graph):
        report = run_structural_validators(duplicate_id_graph)
        assert any(e.code == "DUPLICATE_ID" for e in report.errors)

    def test_bad_edge_reference(self, bad_ref_graph):
        report = validate_edge_references(bad_ref_graph)
        assert len(report.errors) >= 1
        assert any(e.code == "INVALID_REFERENCE" for e in report.errors)

    def test_invalid_node_type(self, invalid_type_graph):
        report = validate_allowed_types(invalid_type_graph)
        codes = {e.code for e in report.errors}
        assert "INVALID_NODE_TYPE" in codes

    def test_invalid_edge_type(self, invalid_type_graph):
        report = validate_allowed_types(invalid_type_graph)
        codes = {e.code for e in report.errors}
        assert "INVALID_EDGE_TYPE" in codes

    def test_required_fields_missing(self):
        data = {"nodes": [{"id": "n1"}], "edges": []}
        report = run_structural_validators(data)
        codes = {e.code for e in report.errors}
        assert "REQUIRED_FIELD" in codes

    def test_self_loop_is_valid_reference(self):
        """A self-loop edge referencing the same node is structurally fine."""
        data = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "n1", "name": "Self", "type": "concept"}],
            "edges": [
                {
                    "id": "e1",
                    "source": "n1",
                    "target": "n1",
                    "type": "SUBCLASS_OF",
                }
            ],
        }
        report = run_structural_validators(data)
        ref_errors = [e for e in report.errors if e.code == "INVALID_REFERENCE"]
        assert len(ref_errors) == 0

    def test_empty_allowed_types_skips_check(self):
        """When allowed lists are empty, type checks are skipped."""
        data = {
            "metadata": {
                "id": "x",
                "name": "x",
                "version": "1",
                "allowed_node_types": [],
                "allowed_edge_types": [],
            },
            "nodes": [{"id": "n1", "name": "Any", "type": "whatever"}],
            "edges": [
                {
                    "id": "e1",
                    "source": "n1",
                    "target": "n1",
                    "type": "ANYTHING",
                }
            ],
        }
        report = run_structural_validators(data)
        type_errors = [
            e
            for e in report.errors
            if e.code in ("INVALID_NODE_TYPE", "INVALID_EDGE_TYPE")
        ]
        assert len(type_errors) == 0


# ---------------------------------------------------------------------------
# Business Rule Validator Tests
# ---------------------------------------------------------------------------


class TestBusinessValidator:
    """Tests for business rule validation."""

    def test_no_cycle_in_acyclic_graph(self, valid_graph):
        report = detect_forbidden_cycles(valid_graph)
        assert report.is_valid

    def test_forbidden_cycle_detected(self, cyclic_graph):
        report = detect_forbidden_cycles(cyclic_graph)
        assert any(e.code == "FORBIDDEN_CYCLE" for e in report.errors)

    def test_cycle_detection_self_loop(self):
        """A self-loop with an acyclic edge type is a cycle."""
        data = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "c1", "name": "Self", "type": "concept"}],
            "edges": [
                {
                    "id": "e1",
                    "source": "c1",
                    "target": "c1",
                    "type": "SUBCLASS_OF",
                }
            ],
        }
        report = detect_forbidden_cycles(data)
        assert any(e.code == "FORBIDDEN_CYCLE" for e in report.errors)

    def test_cycle_not_detected_for_non_acyclic_types(self):
        """Non-acyclic edge types should not trigger cycle detection."""
        data = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [
                {"id": "c1", "name": "A", "type": "concept"},
                {"id": "c2", "name": "B", "type": "concept"},
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "c1",
                    "target": "c2",
                    "type": "HAS_ATTRIBUTE",
                },
                {
                    "id": "e2",
                    "source": "c2",
                    "target": "c1",
                    "type": "HAS_ATTRIBUTE",
                },
            ],
        }
        report = detect_forbidden_cycles(data)
        cycle_errors = [e for e in report.errors if e.code == "FORBIDDEN_CYCLE"]
        assert len(cycle_errors) == 0

    def test_cardinality_default(self):
        """Default max cardinality should not warn on small graphs."""
        data = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "n1", "name": "N1", "type": "concept"}],
            "edges": [
                {"id": f"e{i}", "source": "n1", "target": f"n{i}", "type": "X"}
                for i in range(5)
            ],
        }
        # Add target nodes so references are valid
        data["nodes"] += [
            {"id": f"n{i}", "name": f"T{i}", "type": "concept"} for i in range(5)
        ]
        report = validate_cardinalities(data, max_cardinality=10)
        assert report.is_valid

    def test_cardinality_exceeded(self):
        """Warning when a node has too many edges of the same type."""
        data = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "hub", "name": "Hub", "type": "concept"}],
            "edges": [
                {
                    "id": f"e{i}",
                    "source": "hub",
                    "target": f"t{i}",
                    "type": "LINK",
                }
                for i in range(15)
            ],
        }
        data["nodes"] += [
            {"id": f"t{i}", "name": f"T{i}", "type": "concept"} for i in range(15)
        ]
        report = validate_cardinalities(data, max_cardinality=10)
        assert any(e.code == "CARDINALITY_EXCEEDED" for e in report.errors)

    def test_domain_rule_registration_and_execution(self):
        """Registered domain rules should be executed."""
        clear_domain_rules()

        def my_rule(data):
            return [
                ValidationError(
                    code="MY_RULE",
                    message="Custom rule triggered",
                    severity=Severity.WARNING,
                )
            ]

        register_domain_rule(my_rule)

        from src.services.validation.business_validator import run_business_validators

        data = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [],
            "edges": [],
        }
        report = run_business_validators(data)
        assert any(e.code == "MY_RULE" for e in report.errors)
        clear_domain_rules()

    def test_domain_rule_exception_handling(self):
        """A rule that raises should be caught and reported."""
        clear_domain_rules()

        def broken_rule(data):
            raise ValueError("something broke")

        register_domain_rule(broken_rule)

        from src.services.validation.business_validator import run_business_validators

        data = {
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [],
            "edges": [],
        }
        report = run_business_validators(data)
        assert any(e.code == "DOMAIN_RULE_ERROR" for e in report.errors)
        clear_domain_rules()


# ---------------------------------------------------------------------------
# Integration (validate_graph) Tests
# ---------------------------------------------------------------------------


class TestValidateGraph:
    """Integration tests for the validate_graph entry point."""

    def test_valid_graph_passes_all(self, valid_graph):
        report = validate_graph(valid_graph)
        assert report.is_valid, f"Expected valid, got: {report.errors}"

    def test_duplicate_id_graph(self, duplicate_id_graph):
        report = validate_graph(duplicate_id_graph)
        assert not report.is_valid
        assert any(e.code == "DUPLICATE_ID" for e in report.errors)

    def test_bad_ref_graph(self, bad_ref_graph):
        report = validate_graph(bad_ref_graph)
        assert not report.is_valid
        assert any(e.code == "INVALID_REFERENCE" for e in report.errors)

    def test_cyclic_graph(self, cyclic_graph):
        report = validate_graph(cyclic_graph)
        assert not report.is_valid
        assert any(e.code == "FORBIDDEN_CYCLE" for e in report.errors)

    def test_invalid_type_graph(self, invalid_type_graph):
        report = validate_graph(invalid_type_graph)
        assert not report.is_valid
        codes = {e.code for e in report.errors}
        assert "INVALID_NODE_TYPE" in codes or "INVALID_EDGE_TYPE" in codes


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------


class TestValidationAPI:
    """Tests for the /api/validate endpoints."""

    def test_validate_graph_endpoint_valid(self, client: TestClient, valid_graph):
        response = client.post("/api/validate/graph", json=valid_graph)
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["valid"] is True

    def test_validate_graph_endpoint_invalid(self, client: TestClient, duplicate_id_graph):
        response = client.post("/api/validate/graph", json=duplicate_id_graph)
        assert response.status_code == 200  # validation never 4xx/5xx
        data = response.json()
        assert data["summary"]["valid"] is False
        codes = {e["code"] for e in data["errors"]}
        assert "DUPLICATE_ID" in codes

    def test_validate_graph_endpoint_structure(self, client: TestClient, valid_graph):
        response = client.post("/api/validate/graph", json=valid_graph)
        data = response.json()
        assert "summary" in data
        assert "errors" in data
        assert "total_errors" in data["summary"]
        assert "error_count" in data["summary"]

    def test_validate_graph_missing_body(self, client: TestClient):
        response = client.post("/api/validate/graph", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["valid"] is False

    def test_validate_metamodel_endpoint_not_found(self, client: TestClient):
        """Test that a non-existent metamodel returns 404."""
        response = client.post("/api/validate/nonexistent-id")
        # Should be a 404 because the metamodel is not in DB
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Edge-Case Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Additional edge-case tests."""

    def test_empty_graph(self):
        """A graph with no nodes or edges but valid metadata is valid."""
        data = {
            "metadata": {"id": "e", "name": "Empty", "version": "1.0.0"},
            "nodes": [],
            "edges": [],
        }
        report = validate_graph(data)
        # It should have REQUIRED_FIELD errors because metadata
        # needs allowed_node_types etc? No — allowed_node_types is optional per schema.
        # But required fields check passes since empty nodes/edges are fine.
        # Only structural checks: required metadata fields (id,name,version) present.
        assert report.is_valid

    def test_graph_with_only_required_fields(self):
        """Nodes/edges with only required fields should pass."""
        data = {
            "metadata": {"id": "m1", "name": "Minimal", "version": "1.0.0"},
            "nodes": [{"id": "n1", "name": "N1", "type": "concept"}],
            "edges": [
                {
                    "id": "e1",
                    "source": "n1",
                    "target": "n1",
                    "type": "SUBCLASS_OF",
                }
            ],
        }
        report = validate_graph(data)
        # Self-loop SUBCLASS_OF is a cycle? Yes, SUBCLASS_OF of oneself -> cycle
        # But we expect structural to pass and business to flag the cycle
        structural_ok = all(
            e.code != "REQUIRED_FIELD" for e in report.errors
        )
        assert structural_ok

    def test_special_chars_in_ids(self):
        """IDs with special characters should be handled."""
        data = {
            "metadata": {"id": "m1", "name": "Special", "version": "1.0.0"},
            "nodes": [
                {"id": "n1/x", "name": "Special", "type": "concept"}
            ],
            "edges": [],
        }
        report = validate_graph(data)
        assert report.is_valid

    def test_large_graph_performance(self):
        """Validate a graph with 500 nodes and 500 edges quickly."""
        nodes = [
            {"id": f"n{i}", "name": f"Node{i}", "type": "concept"}
            for i in range(500)
        ]
        edges = [
            {
                "id": f"e{i}",
                "source": f"n{i}",
                "target": f"n{(i+1) % 500}",
                "type": "SUBCLASS_OF",
            }
            for i in range(500)
        ]
        data = {
            "metadata": {"id": "big", "name": "Big", "version": "1.0.0"},
            "nodes": nodes,
            "edges": edges,
        }
        import time

        start = time.time()
        report = validate_graph(data)
        elapsed = time.time() - start
        # Should complete in < 5 seconds
        assert elapsed < 5.0, f"Validation took {elapsed:.2f}s, expected <5s"
        # A 500-node cycle should be detected
        assert not report.is_valid
        assert any(e.code == "FORBIDDEN_CYCLE" for e in report.errors)
