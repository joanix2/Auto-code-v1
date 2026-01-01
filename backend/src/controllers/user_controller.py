"""
Contrôleur FastAPI pour les Users
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from src.models.user import User, UserCreate, UserUpdate, UserResponse
from src.repositories.user_repository import UserRepository
from src.utils.auth import verify_password, create_access_token, get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


class UserLogin(BaseModel):
    """Modèle pour la connexion"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Modèle de réponse pour le token"""
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Connexion d'un utilisateur"""
    try:
        # Récupérer l'utilisateur par username
        user = UserRepository.get_by_username(credentials.username)
        if not user:
            raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect")
        
        # Vérifier le mot de passe
        if not verify_password(credentials.password, user.password):
            raise HTTPException(status_code=401, detail="Nom d'utilisateur ou mot de passe incorrect")
        
        # Créer le token
        access_token = create_access_token(data={"sub": user.username})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la connexion: {str(e)}")


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur connecté"""
    return current_user


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(user: UserCreate):
    """Enregistre un nouvel utilisateur et retourne un token"""
    try:
        # Vérifier si le username existe déjà
        existing_user = UserRepository.get_by_username(user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")
        
        # Créer l'utilisateur
        new_user = UserRepository.create(user)
        
        # Créer le token
        access_token = create_access_token(data={"sub": new_user.username})
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(new_user)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement: {str(e)}")


class GitHubTokenUpdate(BaseModel):
    """Modèle pour la mise à jour du token GitHub"""
    github_token: str


@router.put("/me/github-token", response_model=UserResponse)
async def update_github_token(token_data: GitHubTokenUpdate, current_user: User = Depends(get_current_user)):
    """Met à jour le token GitHub de l'utilisateur"""
    try:
        updated_user = UserRepository.update_github_token(current_user.username, token_data.github_token)
        if not updated_user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        return UserResponse.model_validate(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour du token: {str(e)}")


@router.delete("/me/github-token", response_model=UserResponse)
async def delete_github_token(current_user: User = Depends(get_current_user)):
    """Supprime le token GitHub de l'utilisateur"""
    try:
        updated_user = UserRepository.update_github_token(current_user.username, None)
        if not updated_user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        return UserResponse.model_validate(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression du token: {str(e)}")
