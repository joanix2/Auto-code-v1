"""
Auth Controller - Authentication and OAuth endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import RedirectResponse
import logging
import secrets
from typing import Optional
from pydantic import BaseModel

from ..models.user import User, UserPublic
from ..services.github_oauth_service import GitHubOAuthService
from ..services.user_service import UserService
from ..repositories.user_repository import UserRepository
from ..database import get_db
from ..utils.auth import get_current_user, create_access_token
from ..utils.config import config
from neo4j import AsyncDriver

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


class UserUpdate(BaseModel):
    """User update model"""
    github_token: Optional[str] = None


# Dependency to get UserService with database
def get_user_service(db: AsyncDriver = Depends(get_db)) -> UserService:
    """Get UserService instance with database connection"""
    user_repo = UserRepository(db)
    return UserService(user_repo)


# Dependency to get GitHubOAuthService
def get_oauth_service() -> GitHubOAuthService:
    """Get GitHubOAuthService instance"""
    return GitHubOAuthService()


@router.get("/github/login")
async def github_login(
    oauth_service: GitHubOAuthService = Depends(get_oauth_service)
):
    """
    Redirect to GitHub OAuth login
    
    Returns:
        Redirect to GitHub authorization URL
    """
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    auth_url = oauth_service.get_authorization_url(state)
    logger.info(f"Redirecting to GitHub OAuth")
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: Optional[str] = None,
    oauth_service: GitHubOAuthService = Depends(get_oauth_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Handle GitHub OAuth callback
    
    Args:
        code: OAuth authorization code from GitHub
        state: CSRF state token
        
    Returns:
        Redirect to frontend with access token
    """
    try:
        # Step 1: Exchange code for GitHub access token
        token_response = await oauth_service.exchange_code_for_token(code)
        github_access_token = token_response.get("access_token")
        
        if not github_access_token:
            raise ValueError("No access token received from GitHub")
        
        logger.info("Successfully exchanged code for GitHub token")
        
        # Step 2: Get or create user from GitHub data
        user = await user_service.get_or_create_from_github(github_access_token)
        logger.info(f"User authenticated: {user.username}")
        
        # Step 3: Create JWT token for our application
        jwt_token = create_access_token(data={"sub": user.username, "user_id": user.id})
        
        # Redirect to frontend with token as query parameter
        return RedirectResponse(url=f"{config.FRONTEND_URL}/login?token={jwt_token}")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        # Redirect to frontend with error
        return RedirectResponse(url=f"{config.FRONTEND_URL}/login?error={str(e)}")


@router.get("/me", response_model=UserPublic)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user
    
    Args:
        current_user: Current authenticated user (from JWT)
        
    Returns:
        Current user public information
    """
    return UserPublic.from_user(current_user)


@router.patch("/me", response_model=UserPublic)
async def update_current_user(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current authenticated user
    
    Args:
        update_data: Fields to update (github_token)
        current_user: Current authenticated user (from JWT)
        
    Returns:
        Updated user public information
    """
    update_dict = {}
    
    # Handle github_token update (including None to disconnect)
    if update_data.github_token is not None:
        update_dict["github_token"] = update_data.github_token if update_data.github_token else None
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    updated_user = await user_service.update(current_user.id, update_dict)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User {current_user.username} updated their profile")
    return UserPublic.from_user(updated_user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client should delete token)
    
    Returns:
        Success message
    """
    logger.info(f"User {current_user.username} logged out")
    return {"message": "Successfully logged out"}
