"""
Workflow Conditional Functions
Decision functions for LangGraph conditional edges
"""

import logging
from typing import Literal
from .workflow_state import TicketProcessingState
from .workflow_helpers import MAX_ITERATIONS

logger = logging.getLogger(__name__)


def should_continue_after_check(state: TicketProcessingState) -> Literal["prepare_repository", "create_bug_ticket"]:
    """
    Decide next step after iteration check
    
    Returns:
        "prepare_repository" if OK to continue
        "create_bug_ticket" if max iterations exceeded
    """
    if state.status == "cancelled":
        return "create_bug_ticket"
    return "prepare_repository"


def should_commit(state: TicketProcessingState) -> Literal["commit_changes", "create_bug_ticket", "__end__"]:
    """
    Decide if we should commit changes after LLM call
    
    Returns:
        "commit_changes" if LLM succeeded
        "create_bug_ticket" if failed
        "__end__" if no changes to commit
    """
    if state.status == "failed":
        return "create_bug_ticket"
    
    if state.llm_response and state.llm_response.get("success"):
        return "commit_changes"
    
    return "__end__"


def should_continue_after_ci(state: TicketProcessingState) -> Literal["check_iterations", "await_validation"]:
    """
    Decide next step after CI results
    
    Returns:
        "check_iterations" if CI failed (retry)
        "await_validation" if CI passed (success)
    """
    if state.ci_result and state.ci_result.get("passed"):
        return "await_validation"
    
    # CI failed - increment iteration and retry
    return "check_iterations"


def should_validate_or_retry(state: TicketProcessingState) -> Literal["await_validation", "create_bug_ticket"]:
    """
    Decide if ready for validation or should create bug ticket
    
    Returns:
        "await_validation" if ready for human review
        "create_bug_ticket" if max iterations exceeded
    """
    if state.iteration_count >= MAX_ITERATIONS:
        return "create_bug_ticket"
    
    return "await_validation"
