"""Validation Report — structured error reporting for graph validation.

Provides:
- ValidationError: individual error with code, message, severity, location
- ValidationReport: aggregation of errors with grouping and summary methods
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity level of a validation error."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationError:
    """A single validation error with structured metadata.

    Attributes:
        code: Machine-readable error code (e.g. ``DUPLICATE_ID``).
        message: Human-readable description of the problem.
        severity: Severity level (error / warning / info).
        location: Where the error occurred — node ID, edge ID, or path.
            Can be ``"metadata"``, ``"nodes[3]"``, ``"n1"``, etc.
        suggestion: Optional suggested fix.
    """

    code: str
    message: str
    severity: Severity = Severity.ERROR
    location: str = ""
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict (JSON-safe)."""
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationReport:
    """Aggregated result of running one or more validators.

    Usage::

        report = ValidationReport()
        report.add_error(ValidationError(...))
        report.merge(other_report)

        for error in report.errors:
            print(error.message)

        summary = report.summary()
        grouped = report.group_by_severity()
    """

    errors: list[ValidationError] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_error(self, error: ValidationError) -> None:
        """Append a single error to the report."""
        self.errors.append(error)

    def add_errors(self, errors: list[ValidationError]) -> None:
        """Append multiple errors at once."""
        self.errors.extend(errors)

    def merge(self, other: ValidationReport) -> None:
        """Merge another report's errors into this one."""
        self.errors.extend(other.errors)

    @property
    def is_valid(self) -> bool:
        """``True`` when there are no ERROR-severity issues."""
        return not any(e.severity == Severity.ERROR for e in self.errors)

    @property
    def has_warnings(self) -> bool:
        """``True`` when at least one WARNING-severity issue exists."""
        return any(e.severity == Severity.WARNING for e in self.errors)

    # ------------------------------------------------------------------
    # Analysis helpers
    # ------------------------------------------------------------------

    def group_by_severity(self) -> dict[str, list[ValidationError]]:
        """Return errors grouped by severity level.

        Returns:
            A dict with keys ``"error"``, ``"warning"``, ``"info"``.
        """
        groups: dict[str, list[ValidationError]] = {
            "error": [],
            "warning": [],
            "info": [],
        }
        for err in self.errors:
            groups[err.severity.value].append(err)
        return groups

    def errors_by_code(self, code: str) -> list[ValidationError]:
        """Return all errors with the given code."""
        return [e for e in self.errors if e.code == code]

    def errors_at_location(self, location: str) -> list[ValidationError]:
        """Return all errors that occurred at a specific location."""
        return [e for e in self.errors if e.location == location]

    def summary(self) -> dict[str, Any]:
        """Produce a human-readable summary dict."""
        counts = self.group_by_severity()
        return {
            "valid": self.is_valid,
            "total_errors": len(self.errors),
            "error_count": len(counts["error"]),
            "warning_count": len(counts["warning"]),
            "info_count": len(counts["info"]),
            "has_warnings": self.has_warnings,
        }

    def human_readable(self) -> str:
        """Return a multi-line human-readable summary string."""
        lines: list[str] = []
        if self.is_valid:
            lines.append("✓ Graph is valid.")
        else:
            lines.append("✗ Graph has validation errors.")

        counts = self.group_by_severity()
        lines.append(f"  Errors  : {len(counts['error'])}")
        lines.append(f"  Warnings: {len(counts['warning'])}")
        lines.append(f"  Info    : {len(counts['info'])}")
        lines.append("")

        if self.errors:
            lines.append("Details:")
            for i, err in enumerate(self.errors, 1):
                loc = f" [{err.location}]" if err.location else ""
                lines.append(f"  {i}. [{err.severity.value.upper()}] {err.code}{loc}")
                lines.append(f"     {err.message}")
                if err.suggestion:
                    lines.append(f"     💡 {err.suggestion}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full report to a JSON-safe dict."""
        return {
            "summary": self.summary(),
            "errors": [e.to_dict() for e in self.errors],
        }
