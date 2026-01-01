"""
Contrôleur FastAPI pour les Users
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from src.models.user import User, UserCreate, UserUpdate
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
    user: User


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
            user=user
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la connexion: {str(e)}")


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Récupère les informations de l'utilisateur connecté"""
    return current_user


@router.post("/", response_model=User, status_code=201)
async def create_user(user: UserCreate):
    """Crée un nouvel utilisateur"""
    try:
        # Vérifier si le username existe déjà
        existing_user = UserRepository.get_by_username(user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà")
        
        return UserRepository.create(user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création de l'utilisateur: {str(e)}")


@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum d'éléments à retourner")
):
    """Récupère la liste de tous les utilisateurs"""
    try:
        return UserRepository.get_all(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des utilisateurs: {str(e)}")


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Récupère un utilisateur par son ID"""
    user = UserRepository.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, user: UserUpdate):
    """Met à jour un utilisateur"""
    updated_user = UserRepository.update(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return updated_user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str):
    """Supprime un utilisateur"""
    deleted = UserRepository.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return None
