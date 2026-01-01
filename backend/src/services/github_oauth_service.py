"""
GitHub OAuth Service
Gère l'authentification OAuth2 avec GitHub
"""
import httpx
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class GitHubOAuthService:
    def __init__(self):
        self.client_id = os.getenv("GITHUB_CLIENT_ID")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/auth/github/callback")
        
        if not self.client_id or not self.client_secret:
            raise ValueError("GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in environment variables")
    
    def get_authorization_url(self, state: str) -> str:
        """Génère l'URL d'autorisation GitHub"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "repo user:email",
            "state": state,
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://github.com/login/oauth/authorize?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Échange le code d'autorisation contre un access token"""
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
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Récupère les informations de l'utilisateur GitHub"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            response.raise_for_status()
            return response.json()
