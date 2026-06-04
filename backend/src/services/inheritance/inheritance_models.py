"""Inheritance Models — Pydantic models for graph inheritance configuration.

Defines the data contracts for:
- ``InheritanceType``: FULL, PARTIAL, OVERRIDE
- ``InheritanceConfig``: link between a child graph and its parent
- ``InheritanceTree``: hierarchical tree representation
- ``InheritedElement``: metadata about a single inherited element
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InheritanceType(str, Enum):
    """Type of inheritance from parent to child.

    * **FULL** — child inherits all nodes, edges, and rules from the parent.
      Child can add new elements but cannot remove inherited ones.
    * **PARTIAL** — child inherits only the nodes/edges explicitly referenced
      or matching a selector pattern.
    * **OVERRIDE** — child inherits everything but can override any parent
      element with a local version (child ID wins on conflict).
    """

    FULL = "FULL"
    PARTIAL = "PARTIAL"
    OVERRIDE = "OVERRIDE"


class InheritanceConfig(BaseModel):
    """Configuration for an inheritance link between two graphs.

    Attributes:
        parent_id: Unique identifier of the parent graph.
        child_id: Unique identifier of the child graph.
        inheritance_type: How inheritance is applied (FULL / PARTIAL / OVERRIDE).
        description: Optional human-readable note about this inheritance link.
    """

    parent_id: str = Field(..., description="ID of the parent graph")
    child_id: str = Field(..., description="ID of the child graph")
    inheritance_type: InheritanceType = Field(
        default=InheritanceType.FULL,
        description="Type of inheritance to apply",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of this inheritance link",
    )


class InheritanceTree(BaseModel):
    """Represents a node in the inheritance chain tree.

    Attributes:
        graph_id: ID of this graph in the chain.
        parent_id: ID of the direct parent (None if root).
        depth: Distance from the root (0 for the original root graph).
        child_ids: IDs of graphs that inherit directly from this one.
        inheritance_type: How this graph inherits from its parent.
    """

    graph_id: str = Field(..., description="ID of this graph")
    parent_id: str | None = Field(
        default=None, description="ID of the parent (None if root)"
    )
    depth: int = Field(
        default=0, ge=0, description="Depth from the root of the chain"
    )
    child_ids: list[str] = Field(
        default_factory=list,
        description="IDs of direct children (graphs inheriting from this one)",
    )
    inheritance_type: InheritanceType | None = Field(
        default=None,
        description="How this graph inherits from its parent",
    )


class InheritedElement(BaseModel):
    """Describes the origin and status of an element in an inherited graph.

    Attributes:
        element_id: The ID of the node or edge.
        element_type: Either 'node' or 'edge'.
        source_graph_id: The ID of the graph where this element originates.
        is_overridden: Whether a local definition overrides the inherited one.
        local_modifications: Dict of fields modified locally (if overridden).
        depth: How many levels up the element was inherited from
              (0 = local, 1 = direct parent, 2 = grandparent, etc.).
    """

    element_id: str = Field(..., description="ID of the element")
    element_type: str = Field(
        ..., description="Type of element: 'node' or 'edge'"
    )
    source_graph_id: str = Field(
        ..., description="ID of the originating graph"
    )
    is_overridden: bool = Field(
        default=False,
        description="Whether this element is overridden locally",
    )
    local_modifications: dict[str, Any] = Field(
        default_factory=dict,
        description="Fields modified locally when overridden",
    )
    depth: int = Field(
        default=0,
        ge=0,
        description="Inheritance depth (0 = local, 1+ = inherited)",
    )
