"""
Modèle Pydantic pour les Projects
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ProjectBase(BaseModel):
    """Schéma de base pour un Project"""
    name: str = Field(..., min_length=1, max_length=200, description="Nom du projet")
    description: Optional[str] = Field(None, max_length=1000, description="Description du projet")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Paramètres du projet")


class ProjectCreate(ProjectBase):
    """Schéma pour la création d'un Project"""
    user_id: str = Field(..., description="ID de l'utilisateur propriétaire")


class ProjectUpdate(BaseModel):
    """Schéma pour la mise à jour d'un Project"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = None


class Project(ProjectBase):
    """Schéma complet d'un Project"""
    id: str = Field(..., description="ID unique du projet")
    user_id: str = Field(..., description="ID de l'utilisateur propriétaire")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "project-123",
                "user_id": "user-456",
                "name": "Mon Graphe de Connaissances",
                "description": "Un projet de gestion de connaissances",
                "settings": {
                    "system_prompt": "Tu es un assistant...",
                    "default_layout": "force-directed"
                },
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-02T12:00:00"
            }
        }
