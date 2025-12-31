"""
Main FastAPI application.
Provides REST API for ticket submission and task orchestration.
"""
import uvicorn
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from config import config
from github_client import github_client
from rabbitmq_client import rabbitmq_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Auto-Code Platform API",
    description="Asynchronous development agent platform API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TicketCreate(BaseModel):
    """Model for ticket creation"""
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, description="Ticket description")
    labels: Optional[List[str]] = Field(default=[], description="Issue labels")
    priority: Optional[str] = Field(default="medium", description="Task priority")


class TicketResponse(BaseModel):
    """Model for ticket response"""
    ticket_id: int
    ticket_url: str
    title: str
    status: str
    message: str


class HealthResponse(BaseModel):
    """Model for health check response"""
    status: str
    services: dict


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Auto-Code Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services = {
        "api": "healthy",
        "github": "healthy" if github_client.repo else "not configured",
        "rabbitmq": "healthy"
    }
    
    return {
        "status": "healthy",
        "services": services
    }


@app.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(ticket: TicketCreate):
    """
    Create a new development ticket.
    Creates a GitHub issue and queues the task for processing.
    """
    try:
        # Create GitHub issue
        issue_data = github_client.create_issue(
            title=ticket.title,
            body=ticket.description,
            labels=ticket.labels + ["auto-code"]
        )
        
        if not issue_data:
            raise HTTPException(
                status_code=500,
                detail="Failed to create GitHub issue"
            )
        
        # Prepare task for queue
        task_data = {
            "ticket_id": issue_data["issue_number"],
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "issue_url": issue_data["issue_url"],
            "labels": ticket.labels
        }
        
        # Publish task to RabbitMQ
        success = rabbitmq_client.publish_task(task_data)
        
        if not success:
            # Update issue with error comment
            github_client.update_issue(
                issue_data["issue_number"],
                comment="⚠️ Failed to queue task for processing. Manual intervention required."
            )
            raise HTTPException(
                status_code=500,
                detail="Failed to queue task"
            )
        
        logger.info(f"Successfully created and queued ticket #{issue_data['issue_number']}")
        
        return TicketResponse(
            ticket_id=issue_data["issue_number"],
            ticket_url=issue_data["issue_url"],
            title=issue_data["title"],
            status="queued",
            message="Ticket created and queued for processing"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/tickets/{ticket_id}", response_model=dict)
async def get_ticket(ticket_id: int):
    """Get ticket information"""
    try:
        issue_data = github_client.get_issue(ticket_id)
        
        if not issue_data:
            raise HTTPException(
                status_code=404,
                detail=f"Ticket {ticket_id} not found"
            )
        
        return issue_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ticket: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Auto-Code Platform API...")
    try:
        rabbitmq_client.connect()
        logger.info("API server started successfully")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Auto-Code Platform API...")
    rabbitmq_client.stop()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info"
    )
