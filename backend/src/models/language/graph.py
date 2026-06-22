"""
Language Graph — the core data model for rewriting-logic languages.

A language is defined by nodes of 7 kinds:

  :Sort          — type atomique du domaine (string, int, bool, …)
  :Op            — constructeur de termes (Ticket, User, Invoice, …)
  :Equation      — équation de simplification / normalisation
  :Rule          — règle de transition (inconditionnelle)
  :ConditionalRule — règle conditionnelle
  :Strategy      — contrôle de l'ordre d'application des règles
  :Invariant     — état interdit ou propriété attendue

Un **program** est une instance d'un language : il utilise les sorts
et ops définis par le language, et doit respecter ses invariants.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ──────────────────────────────────────────────
#  Node kinds & Edge kinds
# ──────────────────────────────────────────────


class NodeKind(str, Enum):
    """Les 7 kinds de nœuds d'un language. Chaque valeur est un label Neo4j."""

    SORT = "Sort"
    OP = "Op"
    EQUATION = "Equation"
    RULE = "Rule"
    CONDITIONAL_RULE = "ConditionalRule"
    STRATEGY = "Strategy"
    INVARIANT = "Invariant"


class EdgeKind(str, Enum):
    """Types d'arêtes entre nœuds d'un language."""

    HAS_SORT = "has_sort"
    HAS_PARAM = "has_param"
    SUBSORT = "subsort"
    HAS_LHS = "has_lhs"
    HAS_RHS = "has_rhs"
    HAS_CONDITION = "has_condition"
    HAS_STRATEGY = "has_strategy"
    HAS_INVARIANT = "has_invariant"
    HAS_VALIDATOR = "has_validator"
    EDGE_CONSTRAINT = "edge_constraint"


# ──────────────────────────────────────────────
#  Models
# ──────────────────────────────────────────────


class LangNode(BaseModel):
    """Nœud dans le graphe d'un language. ``kind`` = label Neo4j."""

    id: str = Field(default_factory=lambda: f"n_{uuid.uuid4().hex[:12]}")
    kind: NodeKind
    name: str
    description: str = ""
    properties: dict[str, Any] = Field(default_factory=dict)


class LangEdge(BaseModel):
    """Arête entre deux nœuds du graphe."""

    id: str = Field(default_factory=lambda: f"e_{uuid.uuid4().hex[:12]}")
    kind: EdgeKind
    source_id: str
    target_id: str
    properties: dict[str, Any] = Field(default_factory=dict)


class LangGraph(BaseModel):
    """Graphe d'un language — contient sorts, ops, équations, règles…"""

    nodes: list[LangNode] = Field(default_factory=list)
    edges: list[LangEdge] = Field(default_factory=list)

    # ── builders ──────────────────────────────

    def add_node(self, kind: NodeKind, name: str, description: str = "", **props: Any) -> LangNode:
        node = LangNode(kind=kind, name=name, description=description, properties=props)
        self.nodes.append(node)
        return node

    def add_edge(self, kind: EdgeKind, source_id: str, target_id: str, **props: Any) -> LangEdge:
        edge = LangEdge(kind=kind, source_id=source_id, target_id=target_id, properties=props)
        self.edges.append(edge)
        return edge

    # ── queries ───────────────────────────────

    def nodes_by_kind(self, kind: NodeKind) -> list[LangNode]:
        return [n for n in self.nodes if n.kind == kind]

    def get_node(self, name: str, kind: NodeKind | None = None) -> LangNode | None:
        for n in self.nodes:
            if n.name == name and (kind is None or n.kind == kind):
                return n
        return None

    def get_node_by_id(self, node_id: str) -> LangNode | None:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def edges_by_kind(self, kind: EdgeKind) -> list[LangEdge]:
        return [e for e in self.edges if e.kind == kind]

    def edges_from(self, node_id: str) -> list[LangEdge]:
        return [e for e in self.edges if e.source_id == node_id]

    def edges_to(self, node_id: str) -> list[LangEdge]:
        return [e for e in self.edges if e.target_id == node_id]

    def sub_sorts(self, sort_name: str) -> list[LangNode]:
        parent = self.get_node(sort_name, NodeKind.SORT)
        if not parent:
            return []
        return [
            child
            for e in self.edges_by_kind(EdgeKind.SUBSORT)
            if e.target_id == parent.id
            and (child := self.get_node_by_id(e.source_id))
            and child.kind == NodeKind.SORT
        ]

    def op_result_sort(self, op_id: str) -> LangNode | None:
        for e in self.edges_by_kind(EdgeKind.HAS_SORT):
            if e.source_id == op_id:
                return self.get_node_by_id(e.target_id)
        return None

    def op_params(self, op_id: str) -> list[LangNode]:
        return [
            p
            for e in self.edges_by_kind(EdgeKind.HAS_PARAM)
            if e.source_id == op_id and (p := self.get_node_by_id(e.target_id))
        ]

    def edge_constraints(self) -> list[dict[str, Any]]:
        return [
            {
                "edgeKind": e.properties.get("label", "UNKNOWN"),
                "label": e.properties.get("label", "UNKNOWN"),
                "sourceNodeKind": src.name,
                "targetNodeKind": tgt.name,
                "directed": e.properties.get("directed", True),
            }
            for e in self.edges_by_kind(EdgeKind.EDGE_CONSTRAINT)
            if (src := self.get_node_by_id(e.source_id))
            and (tgt := self.get_node_by_id(e.target_id))
        ]
