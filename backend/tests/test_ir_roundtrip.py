"""Roundtrip tests for the IR JSON schema.

Tests that:
1. An IR graph document validates against the schema
2. Nodes and edges can be serialized and deserialized
3. The schema validation catches malformed documents
4. A real graph structure survives a save-load roundtrip
"""

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.models.graph.schema import IR_SCHEMA, validate_ir_graph

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_ir_graph():
    """A minimal valid IR graph document."""
    return {
        "metadata": {
            "id": "test-graph-001",
            "name": "Test Graph",
            "description": "A minimal test graph",
            "version": "1.0.0",
            "status": "draft",
            "owner_id": "test-user",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": None,
            "node_count": 2,
            "edge_count": 1,
            "allowed_node_types": [],
            "allowed_edge_types": [],
        },
        "nodes": [
            {
                "id": "n1",
                "name": "Person",
                "description": "A person entity",
                "type": "concept",
                "label": "Person",
                "graph_id": "test-graph-001",
                "x": 100.0,
                "y": 200.0,
            },
            {
                "id": "n2",
                "name": "Address",
                "description": "An address",
                "type": "concept",
                "label": "Address",
                "graph_id": "test-graph-001",
                "x": 300.0,
                "y": 200.0,
            },
        ],
        "edges": [
            {
                "id": "subclass_of-n1-n2",
                "description": "Person has an Address",
                "type": "HAS_ATTRIBUTE",
                "label": "HAS_ATTRIBUTE",
                "source": "n1",
                "target": "n2",
                "source_label": "Person",
                "target_label": "Address",
                "directed": True,
                "graph_id": "test-graph-001",
            }
        ],
        "edgeConstraints": [],
    }


@pytest.fixture
def full_ir_graph():
    """A complete IR graph with all node and edge types."""
    return {
        "metadata": {
            "id": "full-graph-001",
            "name": "Full Test Graph",
            "description": "Graph with all node and edge types",
            "version": "2.0.0",
            "status": "validated",
            "owner_id": "admin",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "node_count": 5,
            "edge_count": 4,
            "allowed_node_types": [
                {
                    "name": "concept",
                    "description": "A concept node",
                    "label": "Concept",
                    "labelPlural": "Concepts",
                    "gender": "m",
                    "article": "le",
                },
                {
                    "name": "attribute",
                    "description": "An attribute node",
                    "label": "Attribut",
                    "labelPlural": "Attributs",
                    "gender": "m",
                    "article": "l'",
                },
                {
                    "name": "relation",
                    "description": "A relation node",
                    "label": "Relation",
                    "labelPlural": "Relations",
                    "gender": "f",
                    "article": "la",
                },
            ],
            "allowed_edge_types": [
                {
                    "name": "domain",
                    "description": "Domain edge",
                    "sourceNodeTypes": ["relation"],
                    "targetNodeTypes": ["concept"],
                    "directed": True,
                },
                {
                    "name": "range",
                    "description": "Range edge",
                    "sourceNodeTypes": ["relation"],
                    "targetNodeTypes": ["concept"],
                    "directed": True,
                },
            ],
        },
        "nodes": [
            {
                "id": "c1",
                "name": "Vehicle",
                "description": "A vehicle",
                "type": "concept",
                "label": "Vehicle",
            },
            {
                "id": "c2",
                "name": "Car",
                "description": "A car is a vehicle",
                "type": "concept",
                "label": "Car",
            },
            {
                "id": "a1",
                "name": "speed",
                "description": "Maximum speed",
                "type": "attribute",
                "label": "speed",
                "dataType": "integer",
                "isRequired": True,
                "isUnique": False,
                "concept_id": "c2",
            },
            {
                "id": "r1",
                "name": "is_a",
                "description": "Car is a Vehicle",
                "type": "relation",
                "label": "is_a",
                "relationType": "is_a",
            },
            {
                "id": "c3",
                "name": "Engine",
                "description": "Engine component",
                "type": "concept",
                "label": "Engine",
            },
        ],
        "edges": [
            {
                "id": "subclass_of-c2-c1",
                "type": "SUBCLASS_OF",
                "label": "SUBCLASS_OF",
                "source": "c2",
                "target": "c1",
                "source_label": "Car",
                "target_label": "Vehicle",
                "directed": True,
            },
            {
                "id": "has_attribute-c2-a1",
                "type": "HAS_ATTRIBUTE",
                "label": "HAS_ATTRIBUTE",
                "source": "c2",
                "target": "a1",
                "source_label": "Car",
                "target_label": "speed",
                "directed": True,
            },
            {
                "id": "domain-r1-c2",
                "type": "DOMAIN",
                "label": "DOMAIN",
                "source": "r1",
                "target": "c2",
                "source_label": "is_a",
                "target_label": "Car",
                "directed": True,
            },
            {
                "id": "range-r1-c1",
                "type": "RANGE",
                "label": "RANGE",
                "source": "r1",
                "target": "c1",
                "source_label": "is_a",
                "target_label": "Vehicle",
                "directed": True,
            },
        ],
        "edgeConstraints": [
            {
                "edgeType": "DOMAIN",
                "label": "DOMAIN",
                "sourceNodeType": "relation",
                "targetNodeType": "concept",
                "directed": True,
            },
            {
                "edgeType": "RANGE",
                "label": "RANGE",
                "sourceNodeType": "relation",
                "targetNodeType": "concept",
                "directed": True,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Schema Validation Tests
# ---------------------------------------------------------------------------


class TestSchemaStructure:
    """Tests for the IR JSON Schema structure."""

    def test_schema_is_valid_json_schema(self):
        """The schema itself must be a valid JSON Schema."""
        assert IR_SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert IR_SCHEMA["title"] == "IRGraph"
        assert IR_SCHEMA["type"] == "object"

    def test_schema_has_required_sections(self):
        """Schema must have metadata, nodes, edges, and $defs."""
        assert "metadata" in IR_SCHEMA["properties"]
        assert "nodes" in IR_SCHEMA["properties"]
        assert "edges" in IR_SCHEMA["properties"]
        assert "$defs" in IR_SCHEMA

    def test_schema_defines_node_refs(self):
        """Schema must reference Node and Edge definitions."""
        nodes_items = IR_SCHEMA["properties"]["nodes"]["items"]
        assert "$ref" in nodes_items
        assert nodes_items["$ref"] == "#/$defs/Node"

    def test_schema_defines_node_type(self):
        """NodeType must have required fields."""
        node_type = IR_SCHEMA["$defs"]["NodeType"]
        assert "name" in node_type["required"]
        assert "label" in node_type["required"]
        assert "gender" in node_type["required"]


class TestValidateIRGraph:
    """Tests for validate_ir_graph function."""

    def test_valid_minimal_graph(self, minimal_ir_graph):
        """A minimally valid graph should pass validation."""
        errors = validate_ir_graph(minimal_ir_graph)
        assert errors == []

    def test_valid_full_graph(self, full_ir_graph):
        """A complete graph should pass validation."""
        errors = validate_ir_graph(full_ir_graph)
        assert errors == []

    def test_invalid_root_not_dict(self):
        """A non-dict root should fail."""
        errors = validate_ir_graph("not a dict")
        assert len(errors) > 0

    def test_invalid_missing_metadata(self):
        """Missing metadata should fail."""
        errors = validate_ir_graph({"nodes": [], "edges": []})
        assert any("metadata" in e for e in errors)

    def test_invalid_missing_nodes(self):
        """Missing nodes should fail."""
        errors = validate_ir_graph({"metadata": {"id": "x", "name": "x", "version": "1"}, "edges": []})
        assert any("nodes" in e for e in errors)

    def test_invalid_missing_edges(self):
        """Missing edges should fail."""
        errors = validate_ir_graph({"metadata": {"id": "x", "name": "x", "version": "1"}, "nodes": []})
        assert any("edges" in e for e in errors)

    def test_invalid_metadata_missing_id(self):
        """Metadata without id should fail."""
        errors = validate_ir_graph({
            "metadata": {"name": "x", "version": "1"},
            "nodes": [],
            "edges": [],
        })
        assert any("id" in e for e in errors)

    def test_invalid_node_missing_id(self):
        """Node without id should fail."""
        errors = validate_ir_graph({
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"name": "no-id", "type": "concept"}],
            "edges": [],
        })
        assert any("nodes[0]:" in e and "id" in e for e in errors)

    def test_invalid_node_missing_name(self):
        """Node without name should fail."""
        errors = validate_ir_graph({
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "n1", "type": "concept"}],
            "edges": [],
        })
        assert any("nodes[0]:" in e and "name" in e for e in errors)

    def test_invalid_node_missing_type(self):
        """Node without type should fail."""
        errors = validate_ir_graph({
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "n1", "name": "test"}],
            "edges": [],
        })
        assert any("nodes[0]:" in e and "type" in e for e in errors)

    def test_invalid_edge_missing_fields(self):
        """Edge without required fields should fail."""
        errors = validate_ir_graph({
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [{"id": "n1", "name": "a", "type": "concept"}],
            "edges": [{"id": "e1"}],
        })
        edge_errors = [e for e in errors if "edges[0]:" in e]
        assert len(edge_errors) >= 2  # missing source, target, type

    def test_invalid_nodes_not_list(self):
        """Nodes must be a list."""
        errors = validate_ir_graph({
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": "not a list",
            "edges": [],
        })
        assert any("'nodes' must be an array" in e for e in errors)

    def test_invalid_edges_not_list(self):
        """Edges must be a list."""
        errors = validate_ir_graph({
            "metadata": {"id": "x", "name": "x", "version": "1"},
            "nodes": [],
            "edges": "not a list",
        })
        assert any("'edges' must be an array" in e for e in errors)


# ---------------------------------------------------------------------------
# Serialization Roundtrip Tests
# ---------------------------------------------------------------------------


class TestRoundtrip:
    """Tests for serialization/deserialization roundtrip."""

    def test_json_roundtrip_minimal(self, minimal_ir_graph):
        """Minimal graph survives JSON serialization."""
        serialized = json.dumps(minimal_ir_graph, indent=2, default=str)
        deserialized = json.loads(serialized)
        assert deserialized == minimal_ir_graph

    def test_json_roundtrip_full(self, full_ir_graph):
        """Full graph survives JSON serialization."""
        serialized = json.dumps(full_ir_graph, indent=2, default=str)
        deserialized = json.loads(serialized)
        assert deserialized == full_ir_graph

    def test_json_write_read_file(self, minimal_ir_graph):
        """Writing to a file and reading back should preserve the graph."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(minimal_ir_graph, f, indent=2, default=str)
            f.flush()
            filepath = Path(f.name)

        try:
            restored = json.loads(filepath.read_text(encoding="utf-8"))
            assert restored == minimal_ir_graph
            # Validate after restore
            errors = validate_ir_graph(restored)
            assert errors == []
        finally:
            filepath.unlink(missing_ok=True)

    def test_node_count_consistency(self, full_ir_graph):
        """Node count in metadata should match actual nodes list."""
        assert full_ir_graph["metadata"]["node_count"] == len(full_ir_graph["nodes"])

    def test_edge_count_consistency(self, full_ir_graph):
        """Edge count in metadata should match actual edges list."""
        assert full_ir_graph["metadata"]["edge_count"] == len(full_ir_graph["edges"])

    def test_all_edge_references_exist(self, full_ir_graph):
        """All edge source/target IDs must reference existing nodes."""
        node_ids = {n["id"] for n in full_ir_graph["nodes"]}
        for edge in full_ir_graph["edges"]:
            assert edge["source"] in node_ids, f"Edge {edge['id']}: source {edge['source']} not found"
            assert edge["target"] in node_ids, f"Edge {edge['id']}: target {edge['target']} not found"

    def test_attribute_references_concept(self, full_ir_graph):
        """Attribute nodes with concept_id must reference existing concept IDs."""
        concept_ids = {
            n["id"] for n in full_ir_graph["nodes"] if n["type"] == "concept"
        }
        for node in full_ir_graph["nodes"]:
            if node["type"] == "attribute" and node.get("concept_id"):
                assert node["concept_id"] in concept_ids, (
                    f"Attribute {node['id']} references non-existent concept {node['concept_id']}"
                )


# ---------------------------------------------------------------------------
# Edge Case Tests
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases in IR validation."""

    def test_empty_nodes_and_edges(self):
        """A graph with no nodes or edges is valid if metadata is complete."""
        doc = {
            "metadata": {"id": "empty", "name": "Empty", "version": "1.0.0"},
            "nodes": [],
            "edges": [],
        }
        errors = validate_ir_graph(doc)
        assert errors == []

    def test_missing_optional_metadata_fields(self):
        """Missing optional metadata fields should not cause validation errors."""
        doc = {
            "metadata": {"id": "x", "name": "x", "version": "1.0.0"},
            "nodes": [{"id": "n1", "name": "test", "type": "concept"}],
            "edges": [{
                "id": "e1", "source": "n1", "target": "n1", "type": "SUBCLASS_OF",
            }],
        }
        errors = validate_ir_graph(doc)
        assert errors == []

    def test_self_loop_edge(self):
        """A self-loop edge should be structurally valid."""
        doc = {
            "metadata": {"id": "loop", "name": "Loop", "version": "1.0.0"},
            "nodes": [{"id": "n1", "name": "Self", "type": "concept"}],
            "edges": [{
                "id": "e1", "source": "n1", "target": "n1", "type": "SUBCLASS_OF",
            }],
        }
        errors = validate_ir_graph(doc)
        assert errors == []

    def test_large_node_count(self):
        """A graph with many nodes should validate efficiently."""
        nodes = [
            {"id": f"n{i}", "name": f"Node{i}", "type": "concept"}
            for i in range(1000)
        ]
        edges = []
        doc = {
            "metadata": {"id": "large", "name": "Large", "version": "1.0.0"},
            "nodes": nodes,
            "edges": edges,
        }
        errors = validate_ir_graph(doc)
        assert errors == []

    def test_special_characters_in_names(self):
        """Names with special characters should be valid."""
        doc = {
            "metadata": {"id": "spec", "name": "Spécial & Chars", "version": "1.0.0"},
            "nodes": [{"id": "n1", "name": "Café-Pięć", "type": "concept"}],
            "edges": [],
        }
        errors = validate_ir_graph(doc)
        assert errors == []


# ---------------------------------------------------------------------------
# Schema (JSON) export test
# ---------------------------------------------------------------------------


class TestSchemaExport:
    """Tests that the schema dict can be exported as JSON."""

    def test_schema_serializable(self):
        """The schema must be JSON-serializable (no Python-only types)."""
        serialized = json.dumps(IR_SCHEMA, indent=2)
        assert isinstance(serialized, str)
        deserialized = json.loads(serialized)
        assert deserialized["title"] == "IRGraph"
