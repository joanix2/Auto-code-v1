from typing import List, Optional, Dict, Any
from src.services.base_service import BaseService
from src.repositories.metamodel_repository import MetamodelRepository
from src.models.metamodel import Metamodel, MetamodelCreate, MetamodelUpdate
import logging

logger = logging.getLogger(__name__)


class MetamodelService(BaseService[Metamodel]):
    def __init__(self, repository: MetamodelRepository):
        """
        Initialize metamodel service
        
        Args:
            repository: MetamodelRepository instance
        """
        self.repository = repository

    # Implementation of BaseService interface
    
    async def create(self, data: Dict[str, Any]) -> Metamodel:
        """Create a new metamodel"""
        logger.info(f"🚀 Service: Creating metamodel: {data.get('name')}")
        return await self.repository.create(data)
    
    async def get_by_id(self, entity_id: str) -> Optional[Metamodel]:
        """Get metamodel by ID"""
        logger.info(f"🔍 Service: Getting metamodel by ID: {entity_id}")
        return await self.repository.get_by_id(entity_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Metamodel]:
        """Get all metamodels with optional filters"""
        logger.info(f"🔍 Service: Getting all metamodels with filters: {filters}")
        return await self.repository.get_all()
    
    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[Metamodel]:
        """Update metamodel"""
        logger.info(f"✏️ Service: Updating metamodel: {entity_id}")
        return await self.repository.update(entity_id, update_data)
    
    async def delete(self, entity_id: str) -> bool:
        """Delete metamodel"""
        logger.info(f"🗑️ Service: Deleting metamodel: {entity_id}")
        return await self.repository.delete(entity_id)

    # Custom methods

    async def get_by_name(self, name: str) -> Optional[Metamodel]:
        """Get a metamodel by name"""
        logger.info(f"🔍 Service: Getting metamodel by name: {name}")
        return await self.repository.get_by_name(name)

    async def get_by_status(self, status: str) -> List[Metamodel]:
        """Get all metamodels with a specific status"""
        logger.info(f"🔍 Service: Getting metamodels with status: {status}")
        return await self.repository.get_by_status(status)

    async def get_by_author(self, author: str) -> List[Metamodel]:
        """Get all metamodels by author"""
        logger.info(f"🔍 Service: Getting metamodels by author: {author}")
        return await self.repository.get_by_author(author)

    async def validate_metamodel(self, metamodel_id: str) -> Metamodel:
        """Change metamodel status to validated"""
        logger.info(f"✅ Service: Validating metamodel: {metamodel_id}")
        return await self.update(metamodel_id, {"status": "validated"})

    async def deprecate_metamodel(self, metamodel_id: str) -> Metamodel:
        """Change metamodel status to deprecated"""
        logger.info(f"⚠️ Service: Deprecating metamodel: {metamodel_id}")
        return await self.update(metamodel_id, {"status": "deprecated"})
