"""
Base Controllers - Abstract classes for CRUD operations

- BaseController: Basic CRUD operations (for MDE models, etc.)
- GitHubSyncController: CRUD + GitHub synchronization (for repositories, issues)
"""
from abc import ABC, abstractmethod
from fastapi import HTTPException, status
from typing import List, Optional, TypeVar, Generic, Dict, Any
import logging

from ..models.oauth.user import User

T = TypeVar('T')  # Model type
TCreate = TypeVar('TCreate')  # Create schema type
TUpdate = TypeVar('TUpdate')  # Update schema type

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
    async def validate_create(self, data: TCreate, current_user: User, db) -> TCreate:
        """
        Validate and prepare data for creation
        Returns: Validated data
        Raises: HTTPException if validation fails
        """
        pass
    
    @abstractmethod
    async def validate_update(self, id: str, data: TUpdate, current_user: User, db) -> TUpdate:
        """
        Validate update operation
        Returns: Validated update data
        Raises: HTTPException if validation fails
        """
        pass
    
    # CRUD Operations with common error handling
    
    async def create(self, data: TCreate, current_user: User, db) -> T:
        """
        Create a new resource
        
        Args:
            data: Creation data
            current_user: Current authenticated user
            db: Database connection
            
        Returns:
            Created resource
        """
        try:
            # Validate
            validated_data = await self.validate_create(data, current_user, db)
            
            # Create via service
            resource = await self.service.create(validated_data)
            logger.info(f"Created resource {resource.id if hasattr(resource, 'id') else ''}")
            
            return resource
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create resource: {str(e)}"
            )
    
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
        
        return resource
    
    async def get_all(
        self,
        current_user: User,
        db,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[T]:
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
    
    async def update(
        self,
        resource_id: str,
        updates: TUpdate,
        current_user: User,
        db
    ) -> T:
        """
        Update a resource
        
        Args:
            resource_id: Resource ID
            updates: Fields to update
            current_user: Current authenticated user
            db: Database connection
            
        Returns:
            Updated resource
        """
        try:
            # Validate
            validated_updates = await self.validate_update(resource_id, updates, current_user, db)
            
            # Update via service
            updated_resource = await self.service.update(resource_id, validated_updates)
            
            logger.info(f"Updated resource {resource_id}")
            return updated_resource
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update resource: {str(e)}"
            )
    
    async def delete(self, resource_id: str, current_user: User, db) -> Dict[str, str]:
        """
        Delete a resource
        
        Args:
            resource_id: Resource ID
            current_user: Current authenticated user
            db: Database connection
            
        Returns:
            Success message
        """
        try:
            # Delete via service
            deleted = await self.service.delete(resource_id)
            
            if deleted:
                logger.info(f"Deleted resource {resource_id}")
                return {"message": "Resource deleted successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete resource"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Deletion error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete resource: {str(e)}"
            )


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
    async def generate_id(self, data: Dict[str, Any]) -> str:
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
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[T]:
        """
        Sync resources from GitHub
        Returns: List of synced resources
        """
        pass
    
    # Override create to add ID generation
    async def create(self, data: TCreate, current_user: User, db) -> T:
        """Create with ID generation"""
        try:
            validated_data = await self.validate_create(data, current_user, db)
            
            # Convert to dict and add ID
            data_dict = validated_data.dict() if hasattr(validated_data, 'dict') else dict(validated_data)
            data_dict["id"] = await self.generate_id(data_dict)
            
            resource = await self.service.create(data_dict)
            logger.info(f"Created {self.get_resource_name()} {resource.id}")
            
            return resource
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"{self.get_resource_name().capitalize()} creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create {self.get_resource_name()}: {str(e)}"
            )
    
    # Override delete to use validate_delete
    async def delete(self, resource_id: str, current_user: User, db) -> Dict[str, str]:
        """Delete with validation"""
        try:
            resource = await self.validate_delete(resource_id, current_user, db)
            
            deleted = await self.service.delete(resource_id)
            
            if deleted:
                logger.info(f"Deleted {self.get_resource_name()} {resource_id}")
                return {"message": f"{self.get_resource_name().capitalize()} deleted successfully"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to delete {self.get_resource_name()}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"{self.get_resource_name().capitalize()} deletion error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete {self.get_resource_name()}: {str(e)}"
            )
    
    async def sync(
        self,
        github_token: str,
        current_user: User,
        db,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Sync resources from GitHub
        
        Args:
            github_token: GitHub access token
            current_user: Current authenticated user
            db: Database connection
            **kwargs: Additional sync parameters
            
        Returns:
            Sync result with count and resources
        """
        try:
            if not github_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="GitHub account not connected. Please connect your GitHub account in your profile settings."
                )
            
            resources = await self.sync_from_github(github_token, current_user, **kwargs)
            
            logger.info(f"Synced {len(resources)} {self.get_resource_name_plural()} for {current_user.username}")
            return {
                "count": len(resources),
                self.get_resource_name_plural(): resources
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"{self.get_resource_name().capitalize()} sync error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to sync {self.get_resource_name_plural()}: {str(e)}"
            )
