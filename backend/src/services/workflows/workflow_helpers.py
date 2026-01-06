"""
Workflow Helper Functions
Utility functions for workflow execution
"""

import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_ITERATIONS = 10


async def safe_ws_update(ticket_id: str, status: str, message: str, **kwargs):
    """
    Safely send WebSocket update
    
    Args:
        ticket_id: Ticket ID
        status: Status string
        message: Status message
        **kwargs: Additional parameters
    """
    try:
        # Use absolute import to avoid issues
        try:
            from src.websocket.connection_manager import manager
        except ImportError:
            logger.debug(f"WebSocket manager not available: {message}")
            return
        
        # Send status update
        logger.info(f"[WebSocket] Sending status update to ticket {ticket_id}: {status} - {message}")
        await manager.send_status_update(ticket_id, status, message, **kwargs)
        logger.info(f"[WebSocket] Status update sent successfully")
        
    except Exception as e:
        logger.warning(f"WebSocket update failed: {e}", exc_info=True)


async def safe_ws_log(ticket_id: str, log_type: str, message: str, **kwargs):
    """
    Safely send WebSocket log
    
    Args:
        ticket_id: Ticket ID
        log_type: Log type (info, error, etc)
        message: Log message
        **kwargs: Additional parameters
    """
    try:
        # Use absolute import to avoid issues
        try:
            from src.websocket.connection_manager import manager
        except ImportError:
            logger.debug(f"WebSocket manager not available: {message}")
            return
        
        # Send log
        logger.debug(f"[WebSocket] Sending log: {log_type} - {message}")
        await manager.send_log(ticket_id, log_type, message, **kwargs)
        
    except Exception as e:
        logger.warning(f"WebSocket log failed: {e}", exc_info=True)


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
