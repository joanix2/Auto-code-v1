"""
Attribute Service - Business logic for attributes
"""
from typing import Optional, List, Dict, Any
import logging
from uuid import uuid4

from src.services.base_service import BaseService
from src.repositories.MDE.attribute_repository import AttributeRepository
from src.repositories.MDE.concept_repository import ConceptRepository
from src.models.MDE.attribute import Attribute, AttributeCreate, AttributeUpdate

logger = logging.getLogger(__name__)


class AttributeService(BaseService[Attribute]):
    """Service for attribute operations"""
    
    def __init__(
        self,
        attribute_repo: AttributeRepository,
        concept_repo: ConceptRepository,
        metamodel_repo=None  # Optional for backward compatibility
    ):
        self.attribute_repo = attribute_repo
        self.concept_repo = concept_repo
        self.metamodel_repo = metamodel_repo
    
    async def create(self, data: Dict[str, Any]) -> Attribute:
        """
        Create an attribute
        
        Args:
            data: Attribute creation data (dict)
            
        Returns:
            Created attribute
        """
        # Check if concept exists (if concept_id is provided)
        concept_id = data.get("concept_id")
        if concept_id:
            concept = await self.concept_repo.get_by_id(concept_id)
            if not concept:
                raise ValueError(f"Concept not found: {concept_id}")
            
            # Check for duplicate name in same concept
            name = data.get("name")
            existing = await self.attribute_repo.get_by_name(concept_id, name)
            if existing:
                raise ValueError(f"Attribute with name '{name}' already exists in this concept")
        
        # Prepare data
        attribute_data = {**data}
        attribute_data["id"] = str(uuid4())
        
        # Create attribute (with or without relationship to concept)
        if concept_id:
            attribute = await self.attribute_repo.create_with_relationship(attribute_data)
        else:
            # Create standalone attribute
            attribute = await self.attribute_repo.create(attribute_data)
        
        logger.info(f"Created attribute: {attribute.name} for concept {concept_id}")
        
        return attribute
    
    async def get_by_id(self, attribute_id: str) -> Optional[Attribute]:
        """Get attribute by ID"""
        return await self.attribute_repo.get_by_id(attribute_id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Attribute]:
        """
        Get all attributes with pagination
        
        Args:
            skip: Number of attributes to skip
            limit: Maximum number of attributes to return
            
        Returns:
            List of attributes
        """
        return await self.attribute_repo.get_all(skip, limit)
    
    async def get_by_concept(
        self,
        concept_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attribute]:
        """Get all attributes for a concept"""
        return await self.attribute_repo.get_by_concept(concept_id, skip, limit)
    
    async def get_required_attributes(self, concept_id: str) -> List[Attribute]:
        """Get all required attributes for a concept"""
        return await self.attribute_repo.get_required_attributes(concept_id)
    
    async def update(self, attribute_id: str, update_data: Dict[str, Any]) -> Optional[Attribute]:
        """
        Update an attribute
        
        Args:
            attribute_id: Attribute ID
            update_data: Update data (dict)
            
        Returns:
            Updated attribute or None
        """
        # Remove None values
        updates = {k: v for k, v in update_data.items() if v is not None}
        
        if not updates:
            return await self.get_by_id(attribute_id)
        
        # Check for duplicate name if name is being updated
        if "name" in updates:
            attribute = await self.get_by_id(attribute_id)
            if attribute:
                existing = await self.attribute_repo.get_by_name(attribute.concept_id, updates["name"])
                if existing and existing.id != attribute_id:
                    raise ValueError(f"Attribute with name '{updates['name']}' already exists in this concept")
        
        attribute = await self.attribute_repo.update(attribute_id, updates)
        
        if attribute:
            logger.info(f"Updated attribute: {attribute_id}")
        
        return attribute
    
    async def delete(self, attribute_id: str) -> bool:
        """
        Delete an attribute
        
        Args:
            attribute_id: Attribute ID
            
        Returns:
            True if deleted
        """
        deleted = await self.attribute_repo.delete(attribute_id)
        
        if deleted:
            logger.info(f"Deleted attribute: {attribute_id}")
        
        return deleted
    
    async def count_by_concept(self, concept_id: str) -> int:
        """Count attributes for a concept"""
        return await self.attribute_repo.count_by_concept(concept_id)
