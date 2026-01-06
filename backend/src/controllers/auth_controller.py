"""
Auth Controller - Authentication and OAuth endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
import logging

from ..models.user import User, UserPublic
from ..services.auth import GitHubOAuthService
from ..utils.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.get("/github/login")
async def github_login():
    """
    Redirect to GitHub OAuth login
    
    Returns:
        Redirect to GitHub authorization URL
    """
    oauth_service = GitHubOAuthService()
    auth_url = oauth_service.get_authorization_url()
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(code: str):
    """
    Handle GitHub OAuth callback
    
    Args:
        code: OAuth authorization code from GitHub
        
    Returns:
        User data and access token
    """
    try:
        oauth_service = GitHubOAuthService()
        user, access_token = await oauth_service.handle_callback(code)
        
        return {
            "user": UserPublic(**user.dict()),
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserPublic)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user
    
    Args:
        current_user: Current authenticated user (from JWT)
        
    Returns:
        Current user public information
    """
    return UserPublic(**current_user.dict())


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client should delete token)
    
    Returns:
        Success message
    """
    logger.info(f"User {current_user.username} logged out")
    return {"message": "Successfully logged out"}
