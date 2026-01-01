"""
Modèles pour l'authentification
"""
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token d'accès"""
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Type de token")


class TokenData(BaseModel):
    """Données contenues dans le token"""
    user_id: str = Field(..., description="ID de l'utilisateur")
    username: str = Field(..., description="Nom d'utilisateur")


class LoginRequest(BaseModel):
    """Requête de connexion"""
    username: str = Field(..., min_length=3, description="Nom d'utilisateur")
    password: str = Field(..., min_length=6, description="Mot de passe")


class RegisterRequest(BaseModel):
    """Requête d'inscription"""
    username: str = Field(..., min_length=3, max_length=50, description="Nom d'utilisateur")
    email: str = Field(..., description="Adresse email")
    password: str = Field(..., min_length=6, description="Mot de passe")
    full_name: str | None = Field(None, max_length=100, description="Nom complet")
