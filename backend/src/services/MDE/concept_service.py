"""
Concept Service - Business logic for concepts
"""
from typing import Optional, List, Dict, Any
import logging
from uuid import uuid4

from src.services.base_service import BaseService
from src.repositories.MDE.concept_repository import ConceptRepository
from src.repositories.MDE.metamodel_repository import MetamodelRepository
from src.models.MDE.concept import Concept, ConceptCreate, ConceptUpdate

logger = logging.getLogger(__name__)


class ConceptService(BaseService[Concept]):
    """Service for concept operations"""
    
    def __init__(self, concept_repo: ConceptRepository, metamodel_repo: MetamodelRepository):
        self.concept_repo = concept_repo
        self.metamodel_repo = metamodel_repo
    
    async def create(self, data: Dict[str, Any]) -> Concept:
        """
        Create a concept
        
        Args:
            data: Concept creation data (dict)
            
        Returns:
            Created concept
        """
        # Convert to ConceptCreate if needed
        if not isinstance(data, dict):
            data = data.model_dump()
        
        # Check if metamodel exists (frontend sends graph_id)
        graph_id = data.get("graph_id")
        metamodel = await self.metamodel_repo.get_by_id(graph_id)
        if not metamodel:
            raise ValueError(f"Metamodel not found: {graph_id}")
        
        # Check for duplicate name in same metamodel
        name = data.get("name")
        existing = await self.concept_repo.get_by_name(graph_id, name)
        if existing:
            raise ValueError(f"Concept with name '{name}' already exists in this metamodel")
        
        # Generate ID and create concept
        concept_data = {**data}
        concept_data["id"] = str(uuid4())
        
        logger.info(f"🔍 Creating concept with data: {concept_data}")
        
        # Create concept (repository will create HAS_CONCEPT relationship)
        concept = await self.concept_repo.create(concept_data)
        
        logger.info(f"Created concept: {concept.name} (id={concept.id})")
        
        return concept
    
    async def get_by_id(self, concept_id: str) -> Optional[Concept]:
        """Get concept by ID"""
        return await self.concept_repo.get_by_id(concept_id)
    
    async def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Concept]:
        """
        Get all concepts with optional filters
        
        Args:
            filters: Optional filters (metamodel_id, skip, limit)
            
        Returns:
            List of concepts
        """
        if not filters:
            filters = {}
        
        skip = filters.get("skip", 0)
        limit = filters.get("limit", 100)
        
        # Filter by metamodel
        if "metamodel_id" in filters:
            return await self.concept_repo.get_by_metamodel(filters["metamodel_id"], skip, limit)
        
        # No filters - get all
        return await self.concept_repo.get_all(skip, limit)
    
    async def get_by_metamodel(
        self,
        metamodel_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Concept]:
        """Get all concepts for a metamodel"""
        return await self.concept_repo.get_by_metamodel(metamodel_id, skip, limit)
    
    async def get_with_attributes(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Get concept with all its attributes"""
        return await self.concept_repo.get_with_attributes(concept_id)
    
    async def update(self, concept_id: str, update_data: Dict[str, Any]) -> Optional[Concept]:
        """
        Update a concept
        
        Args:
            concept_id: Concept ID
            update_data: Update data (dict)
            
        Returns:
            Updated concept or None
        """
        # Remove None values
        updates = {k: v for k, v in update_data.items() if v is not None}
        
        if not updates:
            return await self.get_by_id(concept_id)
        
        # Check for duplicate name if name is being updated
        if "name" in updates:
            concept = await self.get_by_id(concept_id)
            if concept:
                existing = await self.concept_repo.get_by_name(concept.metamodel_id, updates["name"])
                if existing and existing.id != concept_id:
                    raise ValueError(f"Concept with name '{updates['name']}' already exists in this metamodel")
        
        concept = await self.concept_repo.update(concept_id, updates)
        
        if concept:
            logger.info(f"Updated concept: {concept_id}")
        
        return concept
    
    async def update_position(self, concept_id: str, x: float, y: float) -> Optional[Concept]:
        """Update concept position in graph visualization"""
        return await self.concept_repo.update_position(concept_id, x, y)
    
    async def delete(self, concept_id: str) -> bool:
        """
        Delete a concept
        
        Args:
            concept_id: Concept ID
            
        Returns:
            True if deleted
        """
        # Get concept first to get metamodel_id
        concept = await self.get_by_id(concept_id)
        if not concept:
            return False
        
        # Delete concept (repository should handle cascade delete of attributes and relationships)
        deleted = await self.concept_repo.delete(concept_id)
        
        if deleted:
            logger.info(f"Deleted concept: {concept_id}")
        
        return deleted
    
    async def count_by_metamodel(self, metamodel_id: str) -> int:
        """Count concepts in a metamodel"""
        return await self.concept_repo.count_by_metamodel(metamodel_id)
