"""
Point d'entrée de l'application FastAPI
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from src.database import db
from src.controllers import (
    auth_controller,
    user_controller, 
    project_controller, 
    classe_controller, 
    individu_controller, 
    relation_controller
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    # Startup
    print("🚀 Démarrage de l'application...")
    db.connect()
    
    if not db.verify_connectivity():
        print("⚠️  Impossible de se connecter à Neo4j. Vérifiez votre configuration.")
    
    yield
    
    # Shutdown
    print("🛑 Arrêt de l'application...")
    db.close()


app = FastAPI(
    title="KGManager API",
    description="API de gestion d'un graphe de connaissances avec Neo4j",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À configurer selon vos besoins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(project_controller.router)
app.include_router(classe_controller.router)
app.include_router(individu_controller.router)
app.include_router(relation_controller.router)


@app.get("/", tags=["root"])
async def root():
    """Endpoint racine"""
    return {
        "message": "Bienvenue sur l'API KGManager",
        "version": "1.0.0",
        "documentation": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Vérification de l'état de l'application"""
    neo4j_status = db.verify_connectivity()
    
    return {
        "status": "healthy" if neo4j_status else "unhealthy",
        "database": {
            "neo4j": "connected" if neo4j_status else "disconnected"
        }
    }


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
