"""Structural Validator — validates the basic structural integrity of an IR graph.

Rules implemented:
1. **Unique IDs** — no duplicate ``id`` across all nodes and edges.
2. **Edge references** — every edge ``source`` / ``target`` points to an existing node.
3. **Allowed types** — node / edge ``type`` must be declared in the allowed lists
   inside ``metadata.allowed_node_types`` / ``metadata.allowed_edge_types``.
4. **Required fields** — every node must have ``id``, ``name``, ``type``;
   every edge must have ``id``, ``source``, ``target``, ``type``.
   (Delegates to the low-level ``validate_ir_graph`` schema check.)
"""

from __future__ import annotations

from typing import Any

from src.models.graph.schema import validate_ir_graph as _schema_validate
from src.services.validation.validation_report import Severity, ValidationError, ValidationReport


def validate_required_fields(data: dict[str, Any]) -> ValidationReport:
    """Check that the graph has the mandatory top-level keys and that
    every node and edge carries its required fields.

    This is a thin wrapper around :func:`src.models.graph.schema.validate_ir_graph`.
    """
    report = ValidationReport()
    schema_errors = _schema_validate(data)

    for msg in schema_errors:
        # Try to guess a meaningful location from the error message
        location = ""
        if "metadata:" in msg:
            location = "metadata"
        elif "nodes[" in msg:
            # Extract e.g. "nodes[3]" from "nodes[3]: missing ..."
            import re

            m = re.search(r"(nodes\[\d+\])", msg)
            if m:
                location = m.group(1)
        elif "edges[" in msg:
            import re

            m = re.search(r"(edges\[\d+\])", msg)
            if m:
                location = m.group(1)

        report.add_error(
            ValidationError(
                code="REQUIRED_FIELD",
                message=msg,
                severity=Severity.ERROR,
                location=location,
                suggestion="Ensure all required fields (id, name, type for nodes; "
                "id, source, target, type for edges) are present.",
            )
        )
    return report


def validate_unique_ids(data: dict[str, Any]) -> ValidationReport:
    """Check that no two nodes or edges share the same ``id``.

    IDs must be unique across the **entire** graph (nodes + edges).
    """
    report = ValidationReport()
    seen: dict[str, list[str]] = {}  # id -> list of locations

    for i, node in enumerate(data.get("nodes", [])):
        nid = node.get("id")
        if nid:
            seen.setdefault(nid, []).append(f"nodes[{i}]")

    for i, edge in enumerate(data.get("edges", [])):
        eid = edge.get("id")
        if eid:
            seen.setdefault(eid, []).append(f"edges[{i}]")

    for obj_id, locations in seen.items():
        if len(locations) > 1:
            report.add_error(
                ValidationError(
                    code="DUPLICATE_ID",
                    message=f"Duplicate ID '{obj_id}' found at: {', '.join(locations)}.",
                    severity=Severity.ERROR,
                    location=locations[0],
                    suggestion=f"Rename or remove the duplicate occurrence of '{obj_id}'.",
                )
            )
    return report


def validate_edge_references(data: dict[str, Any]) -> ValidationReport:
    """Check that every edge's ``source`` and ``target`` reference an existing node."""
    report = ValidationReport()
    node_ids = {n.get("id") for n in data.get("nodes", []) if n.get("id")}

    for i, edge in enumerate(data.get("edges", [])):
        eid = edge.get("id", f"edges[{i}]")
        src = edge.get("source")
        tgt = edge.get("target")

        if src and src not in node_ids:
            report.add_error(
                ValidationError(
                    code="INVALID_REFERENCE",
                    message=f"Edge '{eid}' references non-existent source node '{src}'.",
                    severity=Severity.ERROR,
                    location=eid,
                    suggestion=f"Create node '{src}' or change the edge's source to an existing node.",
                )
            )
        if tgt and tgt not in node_ids:
            report.add_error(
                ValidationError(
                    code="INVALID_REFERENCE",
                    message=f"Edge '{eid}' references non-existent target node '{tgt}'.",
                    severity=Severity.ERROR,
                    location=eid,
                    suggestion=f"Create node '{tgt}' or change the edge's target to an existing node.",
                )
            )
    return report


def validate_allowed_types(data: dict[str, Any]) -> ValidationReport:
    """Check that node / edge types are declared in the allowed lists.

    The allowed lists live in ``metadata.allowed_node_types`` and
    ``metadata.allowed_edge_types``.  If those lists are empty, the check is
    skipped (no constraint declared).
    """
    report = ValidationReport()
    meta = data.get("metadata", {})

    # Build sets of allowed type *names*
    allowed_node_names = {
        nt.get("name") for nt in meta.get("allowed_node_types", []) if nt.get("name")
    }
    allowed_edge_names = {
        et.get("name") for et in meta.get("allowed_edge_types", []) if et.get("name")
    }

    # If nothing declared, skip
    skip_node_check = not allowed_node_names
    skip_edge_check = not allowed_edge_names

    for i, node in enumerate(data.get("nodes", [])):
        ntype = node.get("type")
        if ntype and not skip_node_check and ntype not in allowed_node_names:
            nid = node.get("id", f"nodes[{i}]")
            report.add_error(
                ValidationError(
                    code="INVALID_NODE_TYPE",
                    message=f"Node '{nid}' has type '{ntype}' which is not in "
                    f"allowed_node_types: {sorted(allowed_node_names)}.",
                    severity=Severity.ERROR,
                    location=nid,
                    suggestion=f"Change node type to one of: {', '.join(sorted(allowed_node_names))}, "
                    f"or add '{ntype}' to metadata.allowed_node_types.",
                )
            )

    for i, edge in enumerate(data.get("edges", [])):
        etype = edge.get("type")
        if etype and not skip_edge_check and etype not in allowed_edge_names:
            eid = edge.get("id", f"edges[{i}]")
            report.add_error(
                ValidationError(
                    code="INVALID_EDGE_TYPE",
                    message=f"Edge '{eid}' has type '{etype}' which is not in "
                    f"allowed_edge_types: {sorted(allowed_edge_names)}.",
                    severity=Severity.ERROR,
                    location=eid,
                    suggestion=f"Change edge type to one of: {', '.join(sorted(allowed_edge_names))}, "
                    f"or add '{etype}' to metadata.allowed_edge_types.",
                )
            )
    return report


def run_structural_validators(data: dict[str, Any]) -> ValidationReport:
    """Run all structural validation rules and return the aggregated report.

    This is the single entry point for the structural validation phase.
    """
    report = ValidationReport()
    report.merge(validate_required_fields(data))
    report.merge(validate_unique_ids(data))
    report.merge(validate_edge_references(data))
    report.merge(validate_allowed_types(data))
    return report
