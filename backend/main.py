"""
Main FastAPI application
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.controllers import (
    auth_router,
    copilot_assignment_router,
    issue_router,
    message_router,
    repository_router,
)
from src.controllers.ir_controller import router as ir_router
from src.controllers.dsl.dsl_attribute_controller import router as dsl_attribute_router
from src.controllers.dsl.dsl_concept_controller import router as dsl_concept_router
from src.controllers.dsl.dsl_edge_controller import router as dsl_edge_router
from src.controllers.dsl.dsl_controller import router as dsl_router
from src.controllers.dsl.dsl_relation_controller import router as dsl_relation_router
from src.controllers.dsl.dsl_config_controller import router as dsl_config_router
from src.controllers.inheritance_controller import router as inheritance_router
from src.controllers.ontology_controller import router as ontology_router
from src.controllers.query_controller import router as query_router
from src.controllers.rewrite_controller import router as rewrite_router
from src.controllers.template_controller import router as template_router
from src.controllers.validation_controller import router as validation_router
from src.controllers.codegen_controller import router as codegen_router
from src.controllers.repository.project_controller import router as project_router
from src.controllers.architecture.architecture_controller import router as architecture_router
from src.database import db
from src.utils.config import config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
    lifespan=lifespan,
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
app.include_router(dsl_config_router)
app.include_router(dsl_router)
app.include_router(dsl_concept_router)
app.include_router(dsl_attribute_router)
app.include_router(dsl_relation_router)
app.include_router(dsl_edge_router)
app.include_router(ir_router)
app.include_router(inheritance_router)
app.include_router(query_router)
app.include_router(template_router)
app.include_router(ontology_router)
app.include_router(rewrite_router)
app.include_router(validation_router)
app.include_router(codegen_router)
app.include_router(project_router)
app.include_router(architecture_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Auto-Code Platform API", "version": "2.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    neo4j_status = "healthy" if db.verify_connectivity() else "unhealthy"

    return {
        "status": "healthy" if neo4j_status == "healthy" else "degraded",
        "services": {"api": "healthy", "neo4j": neo4j_status},
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host=config.API_HOST, port=config.API_PORT, reload=True, log_level="info"
    )
