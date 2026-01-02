"""
WebSocket controller for real-time ticket processing updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from src.websocket.connection_manager import manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/tickets/{ticket_id}")
async def websocket_ticket_endpoint(
    websocket: WebSocket,
    ticket_id: str
):
    """
    WebSocket endpoint for receiving real-time updates about a specific ticket.
    
    Usage (JavaScript):
    ```javascript
    const ws = new WebSocket(`ws://localhost:8000/ws/tickets/${ticketId}`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Status update:', data);
        
        // data.type = "status_update" | "log"
        // data.status = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED"
        // data.step = workflow step name
        // data.progress = 0-100
        // data.message = human-readable message
    };
    ```
    
    Args:
        websocket: WebSocket connection
        ticket_id: ID of the ticket to subscribe to
    """
    await manager.connect(websocket, ticket_id)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            f'{{"type": "connected", "ticket_id": "{ticket_id}"}}',
            websocket
        )
        
        # Keep the connection alive and listen for client messages
        while True:
            # Wait for any message from client (heartbeat, etc.)
            data = await websocket.receive_text()
            
            # Echo back for heartbeat/ping-pong
            if data == "ping":
                await manager.send_personal_message(
                    '{"type": "pong"}',
                    websocket
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, ticket_id)
        logger.info(f"WebSocket disconnected for ticket {ticket_id}")
    except Exception as e:
        logger.error(f"WebSocket error for ticket {ticket_id}: {e}")
        manager.disconnect(websocket, ticket_id)


@router.websocket("/tickets")
async def websocket_global_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for receiving updates about all tickets.
    
    Usage (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/tickets');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Global update:', data);
    };
    ```
    
    Args:
        websocket: WebSocket connection
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            '{"type": "connected", "scope": "global"}',
            websocket
        )
        
        # Keep the connection alive
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await manager.send_personal_message(
                    '{"type": "pong"}',
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Global WebSocket disconnected")
    except Exception as e:
        logger.error(f"Global WebSocket error: {e}")
        manager.disconnect(websocket)
