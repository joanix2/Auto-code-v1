"""
GitHub OAuth Service
Handles ONLY OAuth2 authentication flow with GitHub
Does NOT handle user creation/management (that's UserService's job)
"""
import httpx
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class GitHubOAuthService:
    """Service for GitHub OAuth2 authentication flow"""
    
    def __init__(self, redirect_uri: Optional[str] = None):
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        # Allow custom redirect URI for CLI vs web app
        self.redirect_uri = redirect_uri or os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/callback")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in environment variables")
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate GitHub OAuth authorization URL
        
        Args:
            state: Random state for CSRF protection
            
        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "repo user:email",
            "state": state,
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://github.com/login/oauth/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from GitHub callback
            
        Returns:
            Token response with access_token, token_type, scope
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                }
            )
            response.raise_for_status()
            return response.json()
