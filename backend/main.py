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
    auth_router,
    repository_router,
    issue_router,
    message_router,
    copilot_assignment_router,
)
from src.controllers.MDE.metamodel_controller import router as metamodel_router
from src.controllers.MDE.concept_controller import router as concept_router
from src.controllers.MDE.attribute_controller import router as attribute_router

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
app.include_router(auth_router)
app.include_router(repository_router)
app.include_router(issue_router)
app.include_router(message_router)
app.include_router(copilot_assignment_router)
app.include_router(metamodel_router)
app.include_router(concept_router)
app.include_router(attribute_router)


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
