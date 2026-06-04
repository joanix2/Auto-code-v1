"""Formal JSON Schema for the IR (Intermediate Representation) graph format.

This schema defines the contract between all modules:
- API responses
- Frontend graph editor
- File persistence (load/save)
- NetworkX adapter
"""

IR_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://auto-code.dev/schemas/ir-graph.json",
    "title": "IRGraph",
    "description": "Intermediate Representation of a declarative graph program",
    "type": "object",
    "required": ["metadata", "nodes", "edges"],
    "properties": {
        "metadata": {
            "type": "object",
            "description": "Graph metadata (id, name, version, status, etc.)",
            "required": ["id", "name", "version"],
            "properties": {
                "id": {"type": "string", "description": "Unique graph identifier"},
                "name": {"type": "string", "description": "Human-readable graph name"},
                "description": {"type": "string", "description": "Graph description"},
                "version": {"type": "string", "description": "Semantic version"},
                "status": {
                    "type": "string",
                    "enum": ["draft", "validated", "deprecated"],
                    "default": "draft",
                },
                "owner_id": {"type": "string", "description": "Owner/creator identifier"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
                "node_count": {"type": "integer", "minimum": 0},
                "edge_count": {"type": "integer", "minimum": 0},
                "allowed_node_types": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/NodeType"},
                },
                "allowed_edge_types": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/EdgeType"},
                },
            },
        },
        "nodes": {
            "type": "array",
            "description": "All nodes in the graph (concepts, attributes, relations)",
            "items": {"$ref": "#/$defs/Node"},
        },
        "edges": {
            "type": "array",
            "description": "All edges connecting nodes",
            "items": {"$ref": "#/$defs/Edge"},
        },
        "edgeConstraints": {
            "type": "array",
            "description": "Edge type constraints from M3 configuration",
            "items": {
                "type": "object",
                "properties": {
                    "edgeType": {"type": "string"},
                    "label": {"type": "string"},
                    "sourceNodeType": {"type": "string"},
                    "targetNodeType": {"type": "string"},
                    "directed": {"type": "boolean"},
                },
            },
        },
    },
    "$defs": {
        "NodeType": {
            "type": "object",
            "description": "M3 NodeType definition",
            "required": ["name", "label", "labelPlural", "gender", "article"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "label": {"type": "string"},
                "labelPlural": {"type": "string"},
                "gender": {"type": "string", "enum": ["m", "f", "n"]},
                "article": {"type": "string"},
            },
        },
        "EdgeType": {
            "type": "object",
            "description": "M3 EdgeType definition",
            "required": ["name", "sourceNodeTypes", "targetNodeTypes"],
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "sourceNodeTypes": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "targetNodeTypes": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "directed": {"type": "boolean", "default": True},
            },
        },
        "Position": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "X coordinate for visualization"},
                "y": {"type": "number", "description": "Y coordinate for visualization"},
            },
        },
        "Node": {
            "type": "object",
            "description": "A node in the graph (Concept, Attribute, or Relationship)",
            "required": ["id", "name", "type"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "type": {
                    "type": "string",
                    "description": "Node type name (concept, attribute, relation)",
                },
                "label": {"type": "string", "description": "Display label"},
                "graph_id": {"type": "string", "description": "Parent graph ID"},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
            },
        },
        "Edge": {
            "type": "object",
            "description": "An edge connecting two nodes",
            "required": ["id", "source", "target", "type"],
            "properties": {
                "id": {"type": "string"},
                "description": {"type": "string"},
                "type": {
                    "type": "string",
                    "description": "Edge type (DOMAIN, RANGE, HAS_ATTRIBUTE, SUBCLASS_OF)",
                },
                "label": {"type": "string"},
                "source": {"type": "string", "description": "Source node ID"},
                "target": {"type": "string", "description": "Target node ID"},
                "source_label": {"type": "string"},
                "target_label": {"type": "string"},
                "directed": {"type": "boolean", "default": True},
                "graph_id": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"},
            },
        },
    },
}


def validate_ir_graph(data: dict) -> list[str]:
    """Validate an IR graph dict against the schema.

    Returns a list of validation error messages (empty if valid).
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["Root must be a JSON object"]

    for key in ["metadata", "nodes", "edges"]:
        if key not in data:
            errors.append(f"Missing required key: '{key}'")

    if errors:
        return errors

    meta = data["metadata"]
    for field in ["id", "name", "version"]:
        if field not in meta:
            errors.append(f"metadata: missing required field '{field}'")

    if not isinstance(data["nodes"], list):
        errors.append("'nodes' must be an array")
    else:
        for i, node in enumerate(data["nodes"]):
            for field in ["id", "name", "type"]:
                if field not in node:
                    errors.append(f"nodes[{i}]: missing required field '{field}'")

    if not isinstance(data["edges"], list):
        errors.append("'edges' must be an array")
    else:
        for i, edge in enumerate(data["edges"]):
            for field in ["id", "source", "target", "type"]:
                if field not in edge:
                    errors.append(f"edges[{i}]: missing required field '{field}'")

    return errors
