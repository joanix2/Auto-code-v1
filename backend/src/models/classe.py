"""
Modèle Pydantic pour les Classes (types de noeuds)
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ClasseBase(BaseModel):
    """Schéma de base pour une Classe"""
    name: str = Field(..., min_length=1, max_length=100, description="Nom de la classe")
    description: Optional[str] = Field(None, max_length=500, description="Description de la classe")
    color: Optional[str] = Field("#3B82F6", description="Couleur pour la visualisation")
    icon: Optional[str] = Field(None, description="Icône associée")
    properties_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Schéma des propriétés")


class ClasseCreate(ClasseBase):
    """Schéma pour la création d'une Classe"""
    project_id: str = Field(..., description="ID du projet parent")


class ClasseUpdate(BaseModel):
    """Schéma pour la mise à jour d'une Classe"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = None
    icon: Optional[str] = None
    properties_schema: Optional[Dict[str, Any]] = None


class Classe(ClasseBase):
    """Schéma complet d'une Classe"""
    id: str = Field(..., description="ID unique de la classe")
    project_id: str = Field(..., description="ID du projet parent")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "classe-123",
                "project_id": "project-456",
                "name": "Person",
                "description": "Représente une personne",
                "color": "#3B82F6",
                "icon": "user",
                "properties_schema": {
                    "name": {"type": "string", "required": True},
                    "age": {"type": "integer", "required": False}
                },
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-02T12:00:00"
            }
        }
