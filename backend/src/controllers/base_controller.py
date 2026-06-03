"""
Base Controllers - Abstract classes for CRUD operations

- BaseController: Basic CRUD operations (for MDE models, etc.)
- GitHubSyncController: CRUD + GitHub synchronization (for repositories, issues)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from fastapi import HTTPException, status

from ..models.oauth.user import User
from ..utils.error_handler import handle_create, handle_delete, handle_get, handle_operation, handle_update

T = TypeVar("T")  # Model type
TCreate = TypeVar("TCreate")  # Create schema type
TUpdate = TypeVar("TUpdate")  # Update schema type

logger = logging.getLogger(__name__)


class BaseController(ABC, Generic[T, TCreate, TUpdate]):
    """
    Abstract base controller with basic CRUD operations

    Use this for models that don't need GitHub synchronization (MDE models, etc.)

    Provides:
    - CRUD operations (Create, Read, Update, Delete)
    - Common validation and error handling
    """

    def __init__(self, service):
        """
        Args:
            service: Service layer instance (handles business logic)
        """
        self.service = service

    @abstractmethod
    async def validate_create(self, data: TCreate, current_user: User, db) -> TCreate | dict[str, Any]:
        """
        Validate and prepare data for creation
        Returns: Validated data
        Raises: HTTPException if validation fails
        """
        pass

    @abstractmethod
    async def validate_update(self, id: str, data: TUpdate, current_user: User, db) -> TUpdate | dict[str, Any] | None:
        """
        Validate update operation
        Returns: Validated update data
        Raises: HTTPException if validation fails
        """
        pass

    # CRUD Operations with common error handling

    async def create(self, data: TCreate, current_user: User, db) -> T:
        """Create a new resource"""
        async def _perform() -> T:
            validated_data = await self.validate_create(data, current_user, db)
            resource = await self.service.create(validated_data)
            logger.info(f"Created resource {resource.id if hasattr(resource, 'id') else ''}")
            return resource
        return await handle_create(_perform)

    async def get_by_id(self, resource_id: str, current_user: User, db) -> T:
        """
        Get resource by ID

        Args:
            resource_id: Resource ID
            current_user: Current authenticated user
            db: Database connection

        Returns:
            Resource
        """
        resource = await self.service.get_by_id(resource_id)

        if not resource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

        return resource

    async def get_all(
        self, current_user: User, db, skip: int = 0, limit: int = 100, **filters
    ) -> list[T]:
        """
        Get all resources with pagination

        Args:
            current_user: Current authenticated user
            db: Database connection
            skip: Number to skip
            limit: Maximum to return
            **filters: Additional filters

        Returns:
            List of resources
        """
        resources = await self.service.get_all(skip, limit)
        return resources

    async def update(self, resource_id: str, updates: TUpdate, current_user: User, db) -> T:
        """Update a resource"""
        async def _perform() -> T:
            validated_updates = await self.validate_update(resource_id, updates, current_user, db)
            updated_resource = await self.service.update(resource_id, validated_updates)
            logger.info(f"Updated resource {resource_id}")
            return updated_resource
        return await handle_update(_perform)

    async def delete(self, resource_id: str, current_user: User, db) -> dict[str, str]:
        """Delete a resource"""
        async def _perform() -> dict[str, str]:
            deleted = await self.service.delete(resource_id)
            if deleted:
                logger.info(f"Deleted resource {resource_id}")
                return {"message": "Resource deleted successfully"}
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete resource",
            )
        return await handle_delete(_perform)


class GitHubSyncController(BaseController[T, TCreate, TUpdate]):
    """
    Abstract controller with CRUD + GitHub synchronization

    Use this for models that need GitHub synchronization (repositories, issues)

    Extends BaseController with:
    - GitHub synchronization
    - Resource name management
    - ID generation
    """

    @abstractmethod
    def get_resource_name(self) -> str:
        """Return the name of the resource (e.g., 'repository', 'issue')"""
        pass

    @abstractmethod
    def get_resource_name_plural(self) -> str:
        """Return the plural name of the resource (e.g., 'repositories', 'issues')"""
        pass

    @abstractmethod
    async def generate_id(self, data: dict[str, Any]) -> str:
        """Generate a unique ID for the resource"""
        pass

    @abstractmethod
    async def validate_delete(self, resource_id: str, current_user: User, db) -> T:
        """
        Validate delete operation
        Returns: The resource to delete
        Raises: HTTPException if validation fails
        """
        pass

    @abstractmethod
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> list[T]:
        """
        Sync resources from GitHub
        Returns: List of synced resources
        """
        pass

    # Override create to add ID generation
    async def create(self, data: TCreate, current_user: User, db) -> T:
        """Create with ID generation"""
        async def _perform() -> T:
            validated_data = await self.validate_create(data, current_user, db)
            if isinstance(validated_data, dict):
                data_dict = validated_data
            elif hasattr(validated_data, "dict"):
                data_dict = validated_data.dict()
            else:
                data_dict = dict(validated_data)  # type: ignore[arg-type]
            data_dict["id"] = await self.generate_id(data_dict)
            resource = await self.service.create(data_dict)
            logger.info(f"Created {self.get_resource_name()} {resource.id}")
            return resource
        return await handle_create(_perform)

    # Override delete to use validate_delete
    async def delete(self, resource_id: str, current_user: User, db) -> dict[str, str]:
        """Delete with validation"""
        async def _perform() -> dict[str, str]:
            await self.validate_delete(resource_id, current_user, db)
            deleted = await self.service.delete(resource_id)
            if deleted:
                logger.info(f"Deleted {self.get_resource_name()} {resource_id}")
                return {"message": f"{self.get_resource_name().capitalize()} deleted successfully"}
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete {self.get_resource_name()}",
            )
        return await handle_delete(_perform)

    async def sync(self, github_token: str, current_user: User, db, **kwargs) -> dict[str, Any]:
        """Sync resources from GitHub"""
        async def _perform() -> dict[str, Any]:
            if not github_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="GitHub account not connected.",
                )
            resources = await self.sync_from_github(github_token, current_user, **kwargs)
            logger.info(f"Synced {len(resources)} {self.get_resource_name_plural()} for {current_user.username}")
            return {"count": len(resources), self.get_resource_name_plural(): resources}
        return await handle_operation("sync", _perform)
