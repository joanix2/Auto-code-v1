"""
Language Controller — REST API for rewriting-logic languages.

Each language has its own sorts, ops, equations, rules,
conditional rules, strategies, and invariants.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from src.services.language_manager import LanguageManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/languages", tags=["languages"])


def _mgr() -> LanguageManager:
    return LanguageManager()


# ── Language CRUD ──────────────────────────────────────


@router.get("")
async def list_languages():
    return [lang.to_dict() for lang in _mgr().list()]


@router.post("", status_code=201)
async def create_language(data: dict[str, Any]):
    name = data.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    if _mgr().get_by_name(name):
        raise HTTPException(status_code=409, detail=f"Language '{name}' already exists")
    lang = _mgr().create(name, data.get("description", ""))
    return lang.to_dict()


@router.get("/{lang_id}")
async def get_language(lang_id: str):
    lang = _mgr().get(lang_id)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    return lang.to_dict()


@router.delete("/{lang_id}")
async def delete_language(lang_id: str):
    if not _mgr().delete(lang_id):
        raise HTTPException(status_code=404, detail="Language not found or cannot delete last")
    return {"status": "deleted"}


# ── Graph export (for D3.js frontend) ──────────────────


@router.get("/{lang_id}/graph")
async def get_language_graph(lang_id: str):
    lang = _mgr().get(lang_id)
    if not lang:
        raise HTTPException(status_code=404, detail="Language not found")
    g = lang.graph
    return {
        "language": lang.to_dict(),
        "nodes": [
            {
                "id": n.id,
                "kind": n.kind.value,
                "name": n.name,
                "description": n.description,
                **n.properties,
            }
            for n in g.nodes
        ],
        "edges": [
            {
                "id": e.id,
                "kind": e.kind.value,
                "source": e.source_id,
                "target": e.target_id,
                **e.properties,
            }
            for e in g.edges
        ],
    }


# ── Helpers ────────────────────────────────────────────


def _ok(node: LangNode) -> dict:
    return {
        "id": node.id,
        "kind": node.kind.value,
        "name": node.name,
        "description": node.description,
        **node.properties,
    }


# ── Sorts ──────────────────────────────────────────────


@router.get("/{lang_id}/sorts")
async def list_sorts(lang_id: str):
    return [_ok(s) for s in _mgr().get_sorts(lang_id)]


@router.post("/{lang_id}/sorts", status_code=201)
async def create_sort(lang_id: str, data: dict[str, Any]):
    name = data.pop("name", None)
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    desc = data.pop("description", "")
    try:
        s = _mgr().add_sort(lang_id, name, description=desc, **data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _ok(s)


# ── Ops ────────────────────────────────────────────────


@router.get("/{lang_id}/ops")
async def list_ops(lang_id: str):
    return [_ok(o) for o in _mgr().get_ops(lang_id)]


@router.post("/{lang_id}/ops", status_code=201)
async def create_op(lang_id: str, data: dict[str, Any]):
    name = data.pop("name", None)
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    result_sort = data.pop("result_sort", None)
    if not result_sort:
        raise HTTPException(status_code=400, detail="'result_sort' is required")
    params = data.pop("params", [])
    desc = data.pop("description", "")
    try:
        op = _mgr().add_op(lang_id, name, result_sort, params, description=desc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _ok(op)


# ── Equations ──────────────────────────────────────────


@router.get("/{lang_id}/equations")
async def list_equations(lang_id: str):
    return [_ok(e) for e in _mgr().get_equations(lang_id)]


@router.post("/{lang_id}/equations", status_code=201)
async def create_equation(lang_id: str, data: dict[str, Any]):
    name = data.pop("name", None)
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    lhs = data.pop("lhs", "")
    rhs = data.pop("rhs", "")
    desc = data.pop("description", "")
    try:
        eq = _mgr().add_equation(lang_id, name, lhs, rhs, description=desc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _ok(eq)


# ── Rules ──────────────────────────────────────────────


@router.get("/{lang_id}/rules")
async def list_rules(lang_id: str):
    return [_ok(r) for r in _mgr().get_rules(lang_id)]


@router.post("/{lang_id}/rules", status_code=201)
async def create_rule(lang_id: str, data: dict[str, Any]):
    name = data.pop("name", None)
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    lhs = data.pop("lhs", "")
    rhs = data.pop("rhs", "")
    desc = data.pop("description", "")
    try:
        rl = _mgr().add_rule(lang_id, name, lhs, rhs, description=desc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _ok(rl)


# ── Conditional Rules ──────────────────────────────────


@router.get("/{lang_id}/conditional-rules")
async def list_conditional_rules(lang_id: str):
    return [_ok(c) for c in _mgr().get_conditional_rules(lang_id)]


@router.post("/{lang_id}/conditional-rules", status_code=201)
async def create_conditional_rule(lang_id: str, data: dict[str, Any]):
    name = data.pop("name", None)
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    lhs = data.pop("lhs", "")
    rhs = data.pop("rhs", "")
    cond = data.pop("condition", "")
    desc = data.pop("description", "")
    try:
        crl = _mgr().add_conditional_rule(lang_id, name, lhs, rhs, cond, description=desc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _ok(crl)


# ── Strategies ─────────────────────────────────────────


@router.get("/{lang_id}/strategies")
async def list_strategies(lang_id: str):
    return [_ok(s) for s in _mgr().get_strategies(lang_id)]


@router.post("/{lang_id}/strategies", status_code=201)
async def create_strategy(lang_id: str, data: dict[str, Any]):
    name = data.pop("name", None)
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    steps = data.pop("steps", [])
    desc = data.pop("description", "")
    try:
        s = _mgr().add_strategy(lang_id, name, steps, description=desc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _ok(s)


# ── Invariants ─────────────────────────────────────────


@router.get("/{lang_id}/invariants")
async def list_invariants(lang_id: str):
    return [_ok(i) for i in _mgr().get_invariants(lang_id)]


@router.post("/{lang_id}/invariants", status_code=201)
async def create_invariant(lang_id: str, data: dict[str, Any]):
    name = data.pop("name", None)
    if not name:
        raise HTTPException(status_code=400, detail="'name' is required")
    cond = data.pop("condition", "")
    desc = data.pop("description", "")
    try:
        inv = _mgr().add_invariant(lang_id, name, cond, description=desc)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _ok(inv)
