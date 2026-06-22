"""
Language Manager — manages multiple rewriting-logic languages.

Each language is an independent graph containing sorts, ops,
equations, rules, conditional rules, strategies, and invariants.
"""

from __future__ import annotations

import uuid
from typing import Any

from src.models.language import EdgeKind, LangGraph, LangNode, NodeKind


class Language:
    """A rewriting-logic language = a named graph."""

    def __init__(self, name: str, description: str = ""):
        self.id: str = f"lang_{uuid.uuid4().hex[:12]}"
        self.name: str = name
        self.description: str = description
        self.graph: LangGraph = LangGraph()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
        }


class LanguageManager:
    """Singleton that holds all languages."""

    _instance: LanguageManager | None = None
    _languages: dict[str, Language]

    def __new__(cls) -> LanguageManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._languages = {}
            cls._instance._create_default()
        return cls._instance

    def _create_default(self) -> None:
        lang = Language("default", "Default language")
        self._languages[lang.id] = lang

    @classmethod
    def _reset(cls) -> None:
        cls._instance = None

    # ── language CRUD ──────────────────────────

    def create(self, name: str, description: str = "") -> Language:
        lang = Language(name, description)
        self._languages[lang.id] = lang
        return lang

    def get(self, lang_id: str) -> Language | None:
        return self._languages.get(lang_id)

    def get_by_name(self, name: str) -> Language | None:
        for lang in self._languages.values():
            if lang.name == name:
                return lang
        return None

    def list(self) -> list[Language]:
        return list(self._languages.values())

    def delete(self, lang_id: str) -> bool:
        if lang_id in self._languages and len(self._languages) > 1:
            del self._languages[lang_id]
            return True
        return False

    # ── node accessors ─────────────────────────

    def _graph(self, lang_id: str) -> LangGraph | None:
        lang = self.get(lang_id)
        return lang.graph if lang else None

    def get_sorts(self, lang_id: str) -> list[LangNode]:
        g = self._graph(lang_id)
        return g.nodes_by_kind(NodeKind.SORT) if g else []

    def get_ops(self, lang_id: str) -> list[LangNode]:
        g = self._graph(lang_id)
        return g.nodes_by_kind(NodeKind.OP) if g else []

    def get_equations(self, lang_id: str) -> list[LangNode]:
        g = self._graph(lang_id)
        return g.nodes_by_kind(NodeKind.EQUATION) if g else []

    def get_rules(self, lang_id: str) -> list[LangNode]:
        g = self._graph(lang_id)
        return g.nodes_by_kind(NodeKind.RULE) if g else []

    def get_conditional_rules(self, lang_id: str) -> list[LangNode]:
        g = self._graph(lang_id)
        return g.nodes_by_kind(NodeKind.CONDITIONAL_RULE) if g else []

    def get_strategies(self, lang_id: str) -> list[LangNode]:
        g = self._graph(lang_id)
        return g.nodes_by_kind(NodeKind.STRATEGY) if g else []

    def get_invariants(self, lang_id: str) -> list[LangNode]:
        g = self._graph(lang_id)
        return g.nodes_by_kind(NodeKind.INVARIANT) if g else []

    # ── mutations ──────────────────────────────

    def add_sort(self, lang_id: str, name: str, description: str = "", **props: Any) -> LangNode:
        g = self._graph(lang_id)
        if not g:
            raise ValueError(f"Language '{lang_id}' not found")
        return g.add_node(NodeKind.SORT, name, description=description, **props)

    def add_op(
        self,
        lang_id: str,
        name: str,
        result_sort: str,
        params: list[str] | None = None,
        description: str = "",
    ) -> LangNode:
        g = self._graph(lang_id)
        if not g:
            raise ValueError(f"Language '{lang_id}' not found")
        lang = self.get(lang_id)
        result = g.get_node(result_sort, NodeKind.SORT)
        if not result:
            raise ValueError(f"Sort '{result_sort}' not found in language '{lang.name}'")
        op = g.add_node(NodeKind.OP, name, description=description)
        g.add_edge(EdgeKind.HAS_SORT, op.id, result.id)
        for p in params or []:
            pn = g.get_node(p, NodeKind.SORT)
            if pn:
                g.add_edge(EdgeKind.HAS_PARAM, op.id, pn.id)
        return op

    def add_equation(
        self, lang_id: str, name: str, lhs: str = "", rhs: str = "", description: str = ""
    ) -> LangNode:
        g = self._graph(lang_id)
        if not g:
            raise ValueError(f"Language '{lang_id}' not found")
        return g.add_node(NodeKind.EQUATION, name, description=description, lhs=lhs, rhs=rhs)

    def add_rule(
        self, lang_id: str, name: str, lhs: str = "", rhs: str = "", description: str = ""
    ) -> LangNode:
        g = self._graph(lang_id)
        if not g:
            raise ValueError(f"Language '{lang_id}' not found")
        return g.add_node(NodeKind.RULE, name, description=description, lhs=lhs, rhs=rhs)

    def add_conditional_rule(
        self,
        lang_id: str,
        name: str,
        lhs: str = "",
        rhs: str = "",
        condition: str = "",
        description: str = "",
    ) -> LangNode:
        g = self._graph(lang_id)
        if not g:
            raise ValueError(f"Language '{lang_id}' not found")
        return g.add_node(
            NodeKind.CONDITIONAL_RULE,
            name,
            description=description,
            lhs=lhs,
            rhs=rhs,
            condition=condition,
        )

    def add_strategy(
        self, lang_id: str, name: str, steps: list[str] | None = None, description: str = ""
    ) -> LangNode:
        g = self._graph(lang_id)
        if not g:
            raise ValueError(f"Language '{lang_id}' not found")
        return g.add_node(NodeKind.STRATEGY, name, description=description, steps=steps or [])

    def add_invariant(
        self, lang_id: str, name: str, condition: str = "", description: str = ""
    ) -> LangNode:
        g = self._graph(lang_id)
        if not g:
            raise ValueError(f"Language '{lang_id}' not found")
        return g.add_node(NodeKind.INVARIANT, name, description=description, condition=condition)
