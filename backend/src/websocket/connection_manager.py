"""
WebSocket Connection Manager for real-time issue processing updates.
"""
from typing import Dict, Set
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for issue processing updates.
    Clients can subscribe to specific issue IDs to receive real-time updates.
    """
    
    def __init__(self):
        # issue_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Global connections (receive all updates)
        self.global_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, issue_id: str = None):
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            issue_id: Optional issue ID to subscribe to specific updates
        """
        await websocket.accept()
        
        if issue_id:
            if issue_id not in self.active_connections:
                self.active_connections[issue_id] = set()
            self.active_connections[issue_id].add(websocket)
            logger.info(f"WebSocket connected for issue {issue_id}")
        else:
            self.global_connections.add(websocket)
            logger.info("Global WebSocket connected")
    
    def disconnect(self, websocket: WebSocket, issue_id: str = None):
        """
        Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            issue_id: Optional issue ID if subscribed to specific updates
        """
        if issue_id and issue_id in self.active_connections:
            self.active_connections[issue_id].discard(websocket)
            if not self.active_connections[issue_id]:
                del self.active_connections[issue_id]
            logger.info(f"WebSocket disconnected for issue {issue_id}")
        else:
            self.global_connections.discard(websocket)
            logger.info("Global WebSocket disconnected")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        await websocket.send_text(message)
    
    async def broadcast_to_issue(self, issue_id: str, message: dict):
        """
        Broadcast a message to all connections subscribed to a specific issue.
        
        Args:
            issue_id: The issue ID
            message: Message dictionary to send (will be JSON serialized)
        """
        message_str = json.dumps(message)
        
        # Send to issue-specific connections
        if issue_id in self.active_connections:
            connections_to_remove = []
            for connection in self.active_connections[issue_id]:
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    connections_to_remove.append(connection)
            
            # Clean up dead connections
            for connection in connections_to_remove:
                self.active_connections[issue_id].discard(connection)
        
        # Send to global connections
        global_to_remove = []
        for connection in self.global_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.error(f"Error sending message to global WebSocket: {e}")
                global_to_remove.append(connection)
        
        # Clean up dead global connections
        for connection in global_to_remove:
            self.global_connections.discard(connection)
    
    async def send_status_update(self, ticket_id: str, status: str, message: str, 
                                 step: str = None, progress: int = None, 
                                 error: str = None, data: dict = None):
        """
        Send a status update for a ticket.
        
        Args:
            ticket_id: The ticket ID
            status: Status string (e.g., "PENDING", "IN_PROGRESS", "COMPLETED", "FAILED")
            message: Human-readable message
            step: Current workflow step (e.g., "check_iterations", "call_llm")
            progress: Progress percentage (0-100)
            error: Error message if status is FAILED
            data: Additional data to include
        """
        update = {
            "type": "status_update",
            "ticket_id": ticket_id,
            "status": status,
            "message": message,
            "timestamp": None  # Will be set by JSON encoder
        }
        
        if step:
            update["step"] = step
        if progress is not None:
            update["progress"] = progress
        if error:
            update["error"] = error
        if data:
            update["data"] = data
        
        await self.broadcast_to_ticket(ticket_id, update)
    
    async def send_log(self, ticket_id: str, log_level: str, log_message: str):
        """
        Send a log message for a ticket.
        
        Args:
            ticket_id: The ticket ID
            log_level: Log level (INFO, WARNING, ERROR, DEBUG)
            log_message: Log message
        """
        log_event = {
            "type": "log",
            "ticket_id": ticket_id,
            "level": log_level,
            "message": log_message,
            "timestamp": None
        }
        
        await self.broadcast_to_ticket(ticket_id, log_event)


# Global connection manager instance
manager = ConnectionManager()
