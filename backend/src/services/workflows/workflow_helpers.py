"""
Workflow Helper Functions
Utility functions for workflow execution
"""

import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 10


def safe_ws_update(ticket_id: str, status: str, message: str, **kwargs):
    """
    Safely send WebSocket update - skip if no event loop (LangGraph sync nodes)
    
    Args:
        ticket_id: Ticket ID
        status: Status string
        message: Status message
        **kwargs: Additional parameters
    """
    try:
        import asyncio
        from ....websocket.connection_manager import manager
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.send_status_update(ticket_id, status, message, **kwargs))
    except Exception as e:
        logger.debug(f"WebSocket update skipped (no event loop): {message}")


def safe_ws_log(ticket_id: str, log_type: str, message: str, **kwargs):
    """
    Safely send WebSocket log - skip if no event loop (LangGraph sync nodes)
    
    Args:
        ticket_id: Ticket ID
        log_type: Log type (info, error, etc)
        message: Log message
        **kwargs: Additional parameters
    """
    try:
        import asyncio
        from ....websocket.connection_manager import manager
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.send_log(ticket_id, log_type, message, **kwargs))
    except Exception as e:
        logger.debug(f"WebSocket log skipped (no event loop): {message}")


def log_workflow_step(step_name: str, ticket_id: str, details: str = ""):
    """
    Log workflow step with consistent formatting
    
    Args:
        step_name: Name of the workflow step
        ticket_id: Ticket ID
        details: Additional details to log
    """
    logger.info("=" * 80)
    logger.info(f"🔄 [WORKFLOW] {step_name} for ticket {ticket_id}")
    if details:
        logger.info(f"📊 {details}")
    logger.info("=" * 80)


def format_error_message(error: Exception, context: str = "") -> str:
    """
    Format error message for logging and WebSocket
    
    Args:
        error: The exception
        context: Context where error occurred
        
    Returns:
        Formatted error message
    """
    if context:
        return f"{context}: {str(error)}"
    return str(error)
