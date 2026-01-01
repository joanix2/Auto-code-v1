"""
Modèle Pydantic pour les Relations
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class RelationTypeBase(BaseModel):
    """Schéma de base pour un Type de Relation"""
    name: str = Field(..., min_length=1, max_length=100, description="Nom du type de relation")
    description: Optional[str] = Field(None, max_length=500, description="Description")
    color: Optional[str] = Field("#6B7280", description="Couleur pour la visualisation")
    properties_schema: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Schéma des propriétés")


class RelationTypeCreate(RelationTypeBase):
    """Schéma pour la création d'un Type de Relation"""
    project_id: str = Field(..., description="ID du projet parent")


class RelationTypeUpdate(BaseModel):
    """Schéma pour la mise à jour d'un Type de Relation"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = None
    properties_schema: Optional[Dict[str, Any]] = None


class RelationType(RelationTypeBase):
    """Schéma complet d'un Type de Relation"""
    id: str = Field(..., description="ID unique du type de relation")
    project_id: str = Field(..., description="ID du projet parent")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")
    
    class Config:
        from_attributes = True


class RelationBase(BaseModel):
    """Schéma de base pour une Relation"""
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Propriétés de la relation")


class RelationCreate(RelationBase):
    """Schéma pour la création d'une Relation"""
    type_id: str = Field(..., description="ID du type de relation")
    from_individu_id: str = Field(..., description="ID de l'individu source")
    to_individu_id: str = Field(..., description="ID de l'individu cible")
    project_id: str = Field(..., description="ID du projet parent")


class RelationUpdate(BaseModel):
    """Schéma pour la mise à jour d'une Relation"""
    properties: Optional[Dict[str, Any]] = None


class Relation(RelationBase):
    """Schéma complet d'une Relation"""
    id: str = Field(..., description="ID unique de la relation")
    type_id: str = Field(..., description="ID du type de relation")
    from_individu_id: str = Field(..., description="ID de l'individu source")
    to_individu_id: str = Field(..., description="ID de l'individu cible")
    project_id: str = Field(..., description="ID du projet parent")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "relation-123",
                "type_id": "reltype-456",
                "from_individu_id": "individu-789",
                "to_individu_id": "individu-012",
                "project_id": "project-345",
                "properties": {
                    "since": "2020-01-01",
                    "strength": 0.8
                },
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-02T12:00:00"
            }
        }
