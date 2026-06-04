"""Rewrite Service — transforms IR graphs via declarative rewrite rules.

Usage::

    from src.services.rewrite import RewriteEngine, RewriteRule, RewriteResult
    from src.services.rewrite.default_rules import DEFAULT_RULES

    engine = RewriteEngine()
    engine.register_rules(DEFAULT_RULES)

    result = engine.apply_fixpoint(graph_data)
    cleaned_graph = result.modified_graph
"""

from __future__ import annotations

from src.services.rewrite.default_rules import DEFAULT_RULES
from src.services.rewrite.pattern_matcher import match_pattern
from src.services.rewrite.rewrite_engine import RewriteEngine, RewriteResult
from src.services.rewrite.rewrite_rule import RewriteRule

__all__ = [
    "RewriteEngine",
    "RewriteRule",
    "RewriteResult",
    "match_pattern",
    "DEFAULT_RULES",
]
