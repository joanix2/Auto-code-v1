import logging
from abc import ABC, abstractmethod
from typing import Any

from fastapi import HTTPException, status

from ...models.oauth.user import User

logger = logging.getLogger(__name__)


class GitHubSyncMixin(ABC):
    """
    Mixin that adds a GitHub synchronisation contract to any controller.

    Implementations **must** provide:
      - sync_from_github
      - create_on_github
      - update_on_github
      - delete_on_github

    A concrete ``sync()`` wrapper is included for route handlers.
    """

    @abstractmethod
    async def sync_from_github(
        self, github_token: str, current_user: User, db=None, **kwargs
    ) -> list[Any]:
        """Bulk-sync resources from GitHub into the local database."""
        ...

    @abstractmethod
    async def create_on_github(self, data: dict[str, Any]) -> Any:
        """Create a resource on GitHub and return the API response."""
        ...

    @abstractmethod
    async def update_on_github(self, resource_id: str, updates: dict[str, Any]) -> Any:
        """Update a resource on GitHub and return the API response."""
        ...

    @abstractmethod
    async def delete_on_github(self, resource_id: str, **kwargs) -> None:
        """Delete a resource on GitHub."""
        ...

    async def sync(self, github_token: str, current_user: User, db, **kwargs) -> dict[str, Any]:
        """
        Sync resources from GitHub and return a standardised result.

        Wraps :meth:`sync_from_github` with common error handling.
        """
        if not github_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub account not connected.",
            )
        resources = await self.sync_from_github(github_token, current_user, db, **kwargs)
        logger.info("Synced %d resources for user %s", len(resources), current_user.username)
        return {"count": len(resources), "resources": resources}
