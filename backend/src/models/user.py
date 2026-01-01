"""
Modèle Pydantic pour les Users
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Schéma de base pour un User"""
    username: str = Field(..., min_length=3, max_length=50, description="Nom d'utilisateur")
    email: Optional[EmailStr] = Field(None, description="Adresse email")
    full_name: Optional[str] = Field(None, max_length=100, description="Nom complet")
    github_token: Optional[str] = Field(None, description="Token GitHub personnel")
    profile_picture: Optional[str] = Field(None, description="Chemin de la photo de profil")


class UserCreate(BaseModel):
    """Schéma pour la création d'un User"""
    username: str = Field(..., min_length=3, max_length=50, description="Nom d'utilisateur")
    password: str = Field(..., min_length=6, description="Mot de passe")
    email: Optional[EmailStr] = Field(None, description="Adresse email")
    full_name: Optional[str] = Field(None, max_length=100, description="Nom complet")
    name: Optional[str] = Field(None, max_length=100, description="Alias pour full_name")


class UserUpdate(BaseModel):
    """Schéma pour la mise à jour d'un User"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)


class User(UserBase):
    """Schéma complet d'un User (usage interne)"""
    id: str = Field(..., description="ID unique de l'utilisateur")
    password: str = Field(..., description="Mot de passe haché")
    is_active: bool = Field(default=True, description="Utilisateur actif")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")
    
    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schéma de réponse pour un User (sans password)"""
    id: str = Field(..., description="ID unique de l'utilisateur")
    is_active: bool = Field(default=True, description="Utilisateur actif")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: Optional[datetime] = Field(None, description="Date de dernière modification")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "user-123",
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-02T12:00:00"
            }
        }
