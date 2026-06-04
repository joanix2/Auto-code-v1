"""Validation Service — validates IR graph documents.

Usage::

    from src.services.validation import validate_graph

    report = validate_graph(graph_dict)
    if not report.is_valid:
        print(report.human_readable())

The validation pipeline runs in two phases:

1. **Structural** — checks IDs, references, types, required fields.
2. **Business** — checks cardinalities, cycles, domain-specific rules.
"""

from __future__ import annotations

from typing import Any

from src.services.validation.business_validator import (
    DomainRule,
    clear_domain_rules,
    get_domain_rules,
    register_domain_rule,
    run_business_validators,
)
from src.services.validation.structural_validator import run_structural_validators
from src.services.validation.validation_report import ValidationError, ValidationReport, Severity

__all__ = [
    "validate_graph",
    "validate_graph_strict",
    "ValidationReport",
    "ValidationError",
    "Severity",
    "register_domain_rule",
    "clear_domain_rules",
    "get_domain_rules",
    "DomainRule",
]


def validate_graph(data: dict[str, Any]) -> ValidationReport:
    """Run all validators against an IR graph dict.

    This is the main entry point for the validation pipeline.  It runs:

    1. Structural validators (required fields, unique IDs, edge references,
       allowed types).
    2. Business-rule validators (cardinalities, cycles, domain rules).

    Args:
        data: A dict representing an IR graph in the standard JSON format.

    Returns:
        A :class:`ValidationReport` containing all errors/warnings/infos.
    """
    report = ValidationReport()
    report.merge(run_structural_validators(data))
    report.merge(run_business_validators(data))
    return report


def validate_graph_strict(data: dict[str, Any]) -> ValidationReport:
    """Run all validators and additionally warn on unknown extra fields.

    This strict mode is useful for CI / pre-commit hooks where the graph
    should be as clean as possible.
    """
    report = validate_graph(data)

    # Warn about top-level keys that are not part of the schema
    known_keys = {"metadata", "nodes", "edges", "edgeConstraints"}
    extra = set(data.keys()) - known_keys
    for key in sorted(extra):
        report.add_error(
            ValidationError(
                code="UNKNOWN_KEY",
                message=f"Top-level key '{key}' is not recognised by the IR schema.",
                severity=Severity.WARNING,
                location=f"<root>",
                suggestion=f"Remove the key '{key}' or add it to the schema if it is intentional.",
            )
        )
    return report
