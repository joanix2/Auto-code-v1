"""
Base Service - Abstract interfaces for all services
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Dict, Any

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
