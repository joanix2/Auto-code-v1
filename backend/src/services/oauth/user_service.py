"""
User Service - Business logic for user management
"""

import logging
from typing import Any

import httpx

from ...models.oauth.user import User
from ...repositories.oauth.user_repository import UserRepository
from ..base_service import BaseService, SyncableService

logger = logging.getLogger(__name__)


class UserService(BaseService[User], SyncableService[User]):
    """Service for user business logic with GitHub sync"""

    def __init__(self, user_repo: UserRepository):
        """
        Initialize user service

        Args:
            user_repo: User repository instance
        """
        self.user_repo = user_repo

    # Implementation of BaseService interface

    async def create(self, data: dict[str, Any]) -> User:
        """Create a new user in database"""
        return await self.user_repo.create(data)

    async def get_by_id(self, entity_id: str) -> User | None:
        """Get user by ID"""
        return await self.user_repo.get_by_id(entity_id)

    async def get_all(self, skip: int = 0, limit: int = 100, **kwargs) -> list[User]:  # type: ignore[override]
        """Get all users"""
        return await self.user_repo.get_all()

    async def update(self, entity_id: str, update_data: dict[str, Any]) -> User | None:
        """Update user"""
        return await self.user_repo.update(entity_id, update_data)

    async def delete(self, entity_id: str) -> bool:
        """Delete user"""
        return await self.user_repo.delete(entity_id)

    # Implementation of SyncableService interface

    async def fetch_from_github_api(  # type: ignore[override]
        self, access_token: str, username: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Fetch user info from GitHub API without creating DB record

        Args:
            access_token: GitHub access token
            username: Optional username (if not provided, fetches authenticated user)

        Returns:
            List containing user data from GitHub
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        url = (
            f"https://api.github.com/users/{username}"
            if username
            else "https://api.github.com/user"
        )

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            user_data = response.json()

        logger.debug(f"Fetched GitHub user data: {user_data.get('login')}")
        return [user_data]

    async def sync_from_github(self, access_token: str, **kwargs) -> list[User]:
        """
        Sync user from GitHub API and create/update in database

        Args:
            access_token: GitHub access token

        Returns:
            List containing the synced user
        """
        # Fetch from API first
        github_users = await self.fetch_from_github_api(access_token)

        if not github_users:
            return []

        gh_user = github_users[0]

        # Check if user already exists
        existing_user = await self.user_repo.get_by_github_id(gh_user["id"])

        user_data = {
            "github_id": gh_user["id"],
            "username": gh_user["login"],
            "email": gh_user.get("email"),
            "avatar_url": gh_user.get("avatar_url"),
            "github_token": access_token,  # Save the GitHub token
        }

        if existing_user:
            # Update existing user
            user = await self.user_repo.update(existing_user.id, user_data)
            assert user is not None
            logger.info(f"Updated user {user.username} from GitHub")
        else:
            # Create new user
            user_data["id"] = f"user-{gh_user['id']}"
            user = await self.user_repo.create(user_data)
            logger.info(f"Created new user {user.username} from GitHub")

        return [user]

    # Custom methods

    async def get_or_create_from_github(self, access_token: str) -> User:
        """
        Get existing user or create from GitHub (convenience method)

        Args:
            access_token: GitHub access token

        Returns:
            User instance
        """
        users = await self.sync_from_github(access_token)
        return users[0]

    async def get_by_username(self, username: str) -> User | None:
        """Get user by GitHub username"""
        return await self.user_repo.get_by_username(username)

    async def get_by_github_id(self, github_id: int) -> User | None:
        """Get user by GitHub ID"""
        return await self.user_repo.get_by_github_id(github_id)

    async def update_github_token(self, user_id: str, access_token: str) -> User | None:
        """Update user's GitHub access token"""
        user = await self.user_repo.update_github_token(user_id, access_token)

        if user:
            logger.info(f"Updated GitHub token for user {user_id}")

        return user
