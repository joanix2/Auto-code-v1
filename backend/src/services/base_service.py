"""
Base Service - Abstract interfaces for all services
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any
import httpx

T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """Base interface for all services with CRUD operations"""
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity
        
        Args:
            data: Entity data
            
        Returns:
            Created entity
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Get entity by ID
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """
        Get all entities with optional filters
        
        Args:
            filters: Optional filters
            
        Returns:
            List of entities
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update an entity
        
        Args:
            entity_id: Entity ID
            update_data: Fields to update
            
        Returns:
            Updated entity if found
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity
        
        Args:
            entity_id: Entity ID
            
        Returns:
            True if deleted successfully
        """
        pass


class SyncableService(ABC, Generic[T]):
    """Interface for services that can sync with external APIs (GitHub)"""
    
    @abstractmethod
    async def sync_from_github(
        self,
        access_token: str,
        **kwargs
    ) -> List[T]:
        """
        Synchronize entities from GitHub API
        
        Args:
            access_token: GitHub access token
            **kwargs: Additional sync parameters
            
        Returns:
            List of synchronized entities
        """
        pass
    
    @abstractmethod
    async def fetch_from_github_api(
        self,
        access_token: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw data from GitHub API (without creating DB records)
        
        Args:
            access_token: GitHub access token
            **kwargs: API parameters
            
        Returns:
            List of raw GitHub API responses
        """
        pass


class GitHubSyncService(BaseService[T], SyncableService[T], ABC, Generic[T]):
    """
    Abstract service for entities that sync with GitHub and support CRUD operations
    Orchestrates operations between GitHub API and database
    """
    
    # Abstract methods for GitHub API operations (to be implemented by child classes)
    
    @abstractmethod
    async def create_on_github(
        self,
        access_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create entity on GitHub
        
        Args:
            access_token: GitHub access token
            **kwargs: Entity-specific creation parameters
            
        Returns:
            GitHub API response
            
        Raises:
            httpx.HTTPStatusError: If GitHub API call fails
        """
        pass
    
    @abstractmethod
    async def update_on_github(
        self,
        access_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update entity on GitHub
        
        Args:
            access_token: GitHub access token
            **kwargs: Entity-specific update parameters
            
        Returns:
            GitHub API response
            
        Raises:
            httpx.HTTPStatusError: If GitHub API call fails
        """
        pass
    
    @abstractmethod
    async def delete_on_github(
        self,
        access_token: str,
        **kwargs
    ) -> bool:
        """
        Delete entity on GitHub
        
        Args:
            access_token: GitHub access token
            **kwargs: Entity-specific delete parameters
            
        Returns:
            True if deleted successfully
            
        Raises:
            httpx.HTTPStatusError: If GitHub API call fails
        """
        pass
    
    @abstractmethod
    async def map_github_to_db(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map GitHub API response to database entity format
        
        Args:
            github_data: Raw data from GitHub API
            
        Returns:
            Database entity data
        """
        pass
    
    # Template methods for orchestration (can be overridden if needed)
    
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create entity on GitHub AND in database (orchestration)
        
        Expects data to contain 'access_token' key
        """
        access_token = data.pop("access_token")
        
        # 1. Create on GitHub first
        github_response = await self.create_on_github(access_token=access_token, **data)
        
        # 2. Map GitHub response to DB format
        db_data = await self.map_github_to_db(github_response)
        
        # 3. Create in database
        return await self._create_in_db(db_data)
    
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update entity on GitHub AND in database (orchestration)
        
        Expects update_data to optionally contain 'access_token' key
        """
        # 1. Get current entity
        entity = await self.get_by_id(entity_id)
        if not entity:
            return None
        
        access_token = update_data.pop("access_token", None)
        
        # 2. Check if we need to update on GitHub
        github_syncable_fields = self._get_github_syncable_fields()
        needs_github_update = any(field in update_data for field in github_syncable_fields)
        
        if needs_github_update and access_token:
            # Update on GitHub first
            github_response = await self.update_on_github(
                access_token=access_token,
                entity_id=entity_id,
                **update_data
            )
            
            # Map GitHub response to DB format
            db_updates = await self.map_github_to_db(github_response)
            
            # Add any other non-GitHub fields
            for key, value in update_data.items():
                if key not in github_syncable_fields:
                    db_updates[key] = value
            
            # 3. Update in database
            return await self._update_in_db(entity_id, db_updates)
        
        # No GitHub update needed, just update database
        return await self._update_in_db(entity_id, update_data)
    
    async def delete(self, entity_id: str, access_token: Optional[str] = None, **kwargs) -> bool:
        """
        Delete entity on GitHub AND in database (orchestration)
        
        Args:
            entity_id: Entity ID
            access_token: GitHub access token
            **kwargs: Additional parameters to pass to delete_on_github (e.g., repository_full_name)
        """
        # 1. Get current entity
        entity = await self.get_by_id(entity_id)
        if not entity:
            return False
        
        # 2. Delete from GitHub first if token provided
        if access_token:
            try:
                await self.delete_on_github(access_token=access_token, entity_id=entity_id, **kwargs)
            except httpx.HTTPStatusError as e:
                # If it's a 404, the entity is already gone on GitHub, which is fine
                if not (e.response and e.response.status_code == 404):
                    raise
        
        # 3. Delete from database
        return await self._delete_from_db(entity_id)
    
    # Helper methods to be implemented by child classes
    
    @abstractmethod
    async def _create_in_db(self, data: Dict[str, Any]) -> T:
        """Create entity in database"""
        pass
    
    @abstractmethod
    async def _update_in_db(self, entity_id: str, data: Dict[str, Any]) -> Optional[T]:
        """Update entity in database"""
        pass
    
    @abstractmethod
    async def _delete_from_db(self, entity_id: str) -> bool:
        """Delete entity from database"""
        pass
    
    def _get_github_syncable_fields(self) -> List[str]:
        """
        Return list of fields that should be synced with GitHub
        Override in child classes to specify which fields trigger GitHub updates
        
        Returns:
            List of field names that sync with GitHub
        """
        return []

