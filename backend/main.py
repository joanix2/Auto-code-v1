"""
Main FastAPI application
"""
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.database import db
from src.utils.config import config
from src.controllers import (
    user_controller,
    repository_controller,
    ticket_controller,
    github_oauth_controller,
    agent_controller,
    message_controller,
    ticket_processing_controller,
    websocket_controller,
    branch_controller,
    github_issue_controller,
    copilot_development_controller
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("🚀 Starting Auto-Code Platform API...")
    db.connect()
    
    if not db.verify_connectivity():
        logger.warning("⚠️  Unable to connect to Neo4j")
    else:
        logger.info("✓ Neo4j connected")
        db.init_constraints()
        logger.info("✓ Database constraints initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    db.close()
    logger.info("✓ Closed")


app = FastAPI(
    title="Auto-Code Platform API",
    description="API for automated development with AI agents",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user_controller.router, prefix="/api", tags=["users"])
app.include_router(repository_controller.router, prefix="/api", tags=["repositories"])
app.include_router(ticket_controller.router, prefix="/api", tags=["tickets"])
app.include_router(message_controller.router, prefix="/api", tags=["messages"])
app.include_router(branch_controller.router, prefix="/api", tags=["branches"])
app.include_router(agent_controller.router, prefix="/api", tags=["agent"])
app.include_router(ticket_processing_controller.router, prefix="/api", tags=["ticket-processing"])
app.include_router(github_issue_controller.router, prefix="/api/github-issues", tags=["github-issues"])
app.include_router(copilot_development_controller.router, prefix="/api/copilot", tags=["copilot-development"])
app.include_router(websocket_controller.router)  # WebSocket routes
app.include_router(github_oauth_controller.router)  # OAuth routes have their own prefix


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Auto-Code Platform API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    neo4j_status = "healthy" if db.verify_connectivity() else "unhealthy"
    
    return {
        "status": "healthy" if neo4j_status == "healthy" else "degraded",
        "services": {
            "api": "healthy",
            "neo4j": neo4j_status
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info"
    )
