"""
Concept Service - Business logic for concepts
"""
from typing import Optional, List, Dict, Any
import logging
from uuid import uuid4

from src.services.base_service import BaseService
from src.repositories.MDE.concept_repository import ConceptRepository
from src.repositories.MDE.metamodel_repository import MetamodelRepository
from src.models.MDE.M2.concept import Concept, ConceptCreate, ConceptUpdate

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
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Concept]:
        """
        Get all concepts with pagination
        
        Args:
            skip: Number of concepts to skip
            limit: Maximum number of concepts to return
            
        Returns:
            List of concepts
        """
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
        logger.info(f"🔍 ConceptService.update called with concept_id={concept_id}, update_data={update_data}")
        
        # Check if concept exists first
        existing_concept = await self.get_by_id(concept_id)
        logger.info(f"🔍 Existing concept: {existing_concept}")
        
        if not existing_concept:
            logger.error(f"❌ Concept {concept_id} not found in database")
            return None
        
        # Remove None values
        updates = {k: v for k, v in update_data.items() if v is not None}
        
        if not updates:
            logger.info(f"ℹ️ No updates provided, returning existing concept")
            return existing_concept
        
        # Check for duplicate name if name is being updated
        if "name" in updates:
            logger.info(f"🔍 Checking for duplicate name: {updates['name']}")
            existing = await self.concept_repo.get_by_name(existing_concept.metamodel_id, updates["name"])
            if existing and existing.id != concept_id:
                raise ValueError(f"Concept with name '{updates['name']}' already exists in this metamodel")
        
        logger.info(f"🚀 Calling concept_repo.update with id={concept_id}, updates={updates}")
        concept = await self.concept_repo.update(concept_id, updates)
        
        if concept:
            logger.info(f"✅ Updated concept: {concept_id}")
        else:
            logger.error(f"❌ concept_repo.update returned None for {concept_id}")
        
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
        logger.info(f"🔍 ConceptService.delete called for concept_id={concept_id}")
        
        # Get concept first to get metamodel_id
        concept = await self.get_by_id(concept_id)
        logger.info(f"🔍 Concept found: {concept}")
        
        if not concept:
            logger.warning(f"⚠️ Concept {concept_id} not found")
            return False
        
        # Delete concept (repository should handle cascade delete of attributes and relationships)
        logger.info(f"🗑️ Calling concept_repo.delete for {concept_id}")
        deleted = await self.concept_repo.delete(concept_id)
        logger.info(f"🔍 Delete result: {deleted}")
        
        if deleted:
            logger.info(f"✅ Deleted concept: {concept_id}")
        else:
            logger.error(f"❌ Failed to delete concept: {concept_id}")
        
        return deleted
    
    async def count_by_metamodel(self, metamodel_id: str) -> int:
        """Count concepts in a metamodel"""
        return await self.concept_repo.count_by_metamodel(metamodel_id)
