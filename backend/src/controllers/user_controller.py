"""
Contrôleur FastAPI pour les Users
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from src.models.user import User, UserUpdate, UserResponse
from src.repositories.user_repository import UserRepository
from src.utils.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["users"])


# ============================================
# Routes d'authentification classiques DÉSACTIVÉES
# L'authentification se fait uniquement via GitHub OAuth
# ============================================
# @router.post("/login") - Supprimé
# @router.post("/register") - Supprimé
# ============================================


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur connecté"""
    return current_user


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
