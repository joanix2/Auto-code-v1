"""
Agent module for Auto-Code
Implements LangGraph-based AI agents for ticket development
"""

from .base_agent import BaseAgent
from .dummy_agent import DummyAgent

# Claude agent has langgraph dependency issues - lazy import if needed
# from .claude_agent import ClaudeAgent
# from .workflow import DevelopmentWorkflow

__all__ = [
    "BaseAgent",
    "DummyAgent",
    # "ClaudeAgent", 
    # "DevelopmentWorkflow"
]
