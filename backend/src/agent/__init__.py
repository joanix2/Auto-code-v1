"""
Agent module for Auto-Code
Implements AI agents for ticket development
"""

from .base_agent import BaseAgent
from .dummy_agent import DummyAgent
from .simple_claude_agent import SimpleClaudeAgent

__all__ = [
    "BaseAgent",
    "DummyAgent",
    "SimpleClaudeAgent",
]
