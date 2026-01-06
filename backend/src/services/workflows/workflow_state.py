"""
Workflow State Definition
Pydantic models for ticket processing workflow state
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class TicketProcessingState(BaseModel):
    """State for ticket processing workflow"""
    
    # Ticket info
    ticket_id: str
    ticket: Optional[Dict[str, Any]] = None
    repository: Optional[Dict[str, Any]] = None
    
    # Processing state
    status: str = "initialized"  # initialized, preparing, reasoning, testing, validation, completed, failed
    iteration_count: int = 0
    
    # Paths
    repo_path: Optional[str] = None
    branch_name: Optional[str] = None
    
    # Conversation
    messages: list = Field(default_factory=list)
    last_message: Optional[Dict[str, Any]] = None
    
    # Results
    llm_response: Optional[Dict[str, Any]] = None
    ci_result: Optional[Dict[str, Any]] = None
    commit_hash: Optional[str] = None
    
    # Errors
    errors: list = Field(default_factory=list)
    
    # Final result
    success: bool = False
    final_status: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
