"""
Modèle Pydantic pour les Individus (instances de noeuds)
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class IndividuBase(BaseModel):
    """Schéma de base pour un Individu"""
    label: str = Field(..., min_length=1, max_length=200, description="Label de l'individu")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Propriétés de l'individu")


class IndividuCreate(IndividuBase):
    """Schéma pour la création d'un Individu"""
    classe_id: str = Field(..., description="ID de la classe (type)")
    project_id: str = Field(..., description="ID du projet parent")


class IndividuUpdate(BaseModel):
    """Schéma pour la mise à jour d'un Individu"""
    label: Optional[str] = Field(None, min_length=1, max_length=200)
    properties: Optional[Dict[str, Any]] = None


class Individu(IndividuBase):
    """Schéma complet d'un Individu"""
    id: str = Field(..., description="ID unique de l'individu")
    classe_id: str = Field(..., description="ID de la classe (type)")
    project_id: str = Field(..., description="ID du projet parent")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "individu-123",
                "classe_id": "classe-456",
                "project_id": "project-789",
                "label": "John Doe",
                "properties": {
                    "name": "John Doe",
                    "age": 30,
                    "email": "john@example.com"
                },
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-02T12:00:00"
            }
        }
