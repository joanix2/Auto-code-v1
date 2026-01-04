"""
GitHub OAuth Controller
Endpoints pour l'authentification OAuth2 avec GitHub
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from src.services.github_oauth_service import GitHubOAuthService
from src.repositories.user_repository import UserRepository
from src.utils.auth import create_access_token, get_current_user
from src.models.user import User, UserCreate
import secrets
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/github", tags=["github-oauth"])

# Store temporaire pour les states (en production, utiliser Redis)
pending_states = {}


@router.get("/login")
async def github_login():
    """Initie le flux OAuth2 avec GitHub"""
    try:
        github_oauth_service = GitHubOAuthService()
        state = secrets.token_urlsafe(32)
        pending_states[state] = True
        
        auth_url = github_oauth_service.get_authorization_url(state)
        return {"auth_url": auth_url}
    except ValueError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"GitHub OAuth not configured: {str(e)}"
        )


@router.get("/callback")
async def github_callback(
    code: str = Query(...),
    state: str = Query(...)
):
    """Callback après l'autorisation GitHub"""
    
    # Vérifier le state pour prévenir les attaques CSRF
    if state not in pending_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    del pending_states[state]
    
    try:
        github_oauth_service = GitHubOAuthService()
        
        # Échanger le code contre un token
        token_data = await github_oauth_service.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")
        
        # Récupérer les infos utilisateur GitHub
        github_user = await github_oauth_service.get_user_info(access_token)
        
        # Chercher d'abord par email pour éviter les doublons
        user = None
        if github_user.get("email"):
            user = UserRepository.get_by_email(github_user["email"])
            if user:
                logger.info(f"Found existing user by email: {user.username}")
        
        # Si pas trouvé par email, chercher par username GitHub
        if not user:
            user = UserRepository.get_by_username(github_user["login"])
        
        if not user:
            # Créer un nouvel utilisateur
            user_data = UserCreate(
                username=github_user["login"],
                email=github_user.get("email"),
                full_name=github_user.get("name"),
                password=secrets.token_urlsafe(32)  # Mot de passe aléatoire (non utilisé pour OAuth)
            )
            user = UserRepository.create(user_data)
            logger.info(f"New user created via GitHub OAuth: {user.username}")
        else:
            logger.info(f"Existing user logged in via GitHub OAuth: {user.username}")
        
        # Mettre à jour le token GitHub et la photo de profil
        UserRepository.update_github_token(user.username, access_token)
        if github_user.get("avatar_url"):
            # Mettre à jour la photo de profil
            UserRepository.update_profile_picture(user.username, github_user["avatar_url"])
        
        # Créer notre JWT
        jwt_token = create_access_token({"sub": user.username})
        
        # Rediriger vers le frontend avec le token
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?token={jwt_token}",
            status_code=302
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth error: {str(e)}", exc_info=True)
        # Rediriger vers le frontend avec une erreur
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{frontend_url}/login?error=oauth_failed",
            status_code=302
        )


@router.delete("/disconnect")
async def disconnect_github(
    current_user: User = Depends(get_current_user)
):
    """Déconnecte le compte GitHub"""
    UserRepository.update_github_token(current_user.username, None)
    logger.info(f"User {current_user.username} disconnected GitHub account")
    return {"message": "GitHub account disconnected"}
