"""
Base Controller - Abstract class for CRUD + Sync operations
"""
from abc import ABC, abstractmethod
from fastapi import HTTPException, status
from typing import List, Optional, TypeVar, Generic, Dict, Any
import logging

from ..models.user import User
from ..repositories.base import BaseRepository

T = TypeVar('T')  # Model type
TCreate = TypeVar('TCreate')  # Create schema type
TUpdate = TypeVar('TUpdate')  # Update schema type

logger = logging.getLogger(__name__)


class BaseController(ABC, Generic[T, TCreate, TUpdate]):
    """
    Abstract base controller with CRUD + Sync operations
    
    Provides:
    - CRUD operations (Create, Read, Update, Delete)
    - Sync from GitHub
    - Common validation and error handling
    """
    
    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository
    
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
    async def validate_create(self, data: TCreate, current_user: User, db) -> Dict[str, Any]:
        """
        Validate and prepare data for creation
        Returns: Dict with validated data ready for repository
        Raises: HTTPException if validation fails
        """
        pass
    
    @abstractmethod
    async def validate_update(self, resource_id: str, updates: TUpdate, current_user: User, db) -> Optional[Dict[str, Any]]:
        """
        Validate update operation. Can return modified update data if needed (e.g., after GitHub sync).
        Returns: None or Dict with validated/modified update data
        Raises: HTTPException if validation fails
        """
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
            # Validate and prepare data
            validated_data = await self.validate_create(data, current_user, db)
            
            # Generate ID
            validated_data["id"] = await self.generate_id(validated_data)
            
            # Create resource
            resource = await self.repository.create(validated_data)
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
        resource = await self.repository.get_by_id(resource_id)
        
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.get_resource_name().capitalize()} not found"
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
        resources = await self.repository.get_all(skip, limit)
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
            # Validate update (may return modified data after GitHub sync)
            validated_updates = await self.validate_update(resource_id, updates, current_user, db)
            
            # Use validated data if returned, otherwise use original updates
            update_data = validated_updates if validated_updates is not None else updates.dict(exclude_unset=True)
            
            # Update resource
            updated_resource = await self.repository.update(
                resource_id,
                update_data
            )
            
            logger.info(f"Updated {self.get_resource_name()} {resource_id}")
            return updated_resource
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"{self.get_resource_name().capitalize()} update error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update {self.get_resource_name()}: {str(e)}"
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
            # Validate delete
            resource = await self.validate_delete(resource_id, current_user, db)
            
            # Delete resource
            deleted = await self.repository.delete(resource_id)
            
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
