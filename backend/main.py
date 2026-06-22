"""
Main FastAPI application — rewriting-logic platform.
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
from src.controllers.language_controller import router as language_router
from src.controllers.rewrite_controller import router as rewrite_router
from src.controllers.template_controller import router as template_router
from src.controllers.validation_controller import router as validation_router
from src.controllers.codegen_controller import router as codegen_router
from src.database import db
from src.utils.config import config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting...")
    db.connect()

    if not db.verify_connectivity():
        logger.warning("⚠️  Could not connect to Neo4j")
    else:
        logger.info("✓ Neo4j connected")
        db.init_constraints()
        logger.info("✓ Database constraints initialized")

    yield

    logger.info("🛑 Shutting down...")
    db.close()
    logger.info("✓ Closed")


app = FastAPI(
    title="Auto-Code Platform API",
    description="Rewriting-logic language platform",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(repository_router)
app.include_router(issue_router)
app.include_router(message_router)
app.include_router(copilot_assignment_router)
app.include_router(language_router)
app.include_router(rewrite_router)
app.include_router(template_router)
app.include_router(validation_router)
app.include_router(codegen_router)


@app.get("/")
async def root():
    return {"message": "Auto-Code Platform API", "version": "3.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": {"api": "healthy"}}


if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
