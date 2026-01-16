"""
Relationship Controller - API endpoints for relationships with ontological reasoning
"""
from fastapi import HTTPException, status
from typing import List, Dict, Any, Optional
import logging
from uuid import uuid4

from ..base_controller import BaseController
from src.services.MDE.relationship_service import RelationshipService
from src.models.MDE.relationship import (
    Relationship,
    RelationshipType,
    RelationshipCreate,
    RelationshipUpdate
)
from src.models.user import User

logger = logging.getLogger(__name__)


class RelationshipController(BaseController[Relationship, RelationshipCreate, RelationshipUpdate]):
    """Controller for relationship CRUD operations with ontological reasoning"""
    
    def __init__(self, service: RelationshipService):
        self.service = service
    
    def get_resource_name(self) -> str:
        return "relationship"
    
    def get_resource_name_plural(self) -> str:
        return "relationships"
    
    async def generate_id(self, data: Dict[str, Any]) -> str:
        """Generate unique ID for relationship"""
        return str(uuid4())
    
    async def validate_create(self, data: RelationshipCreate, current_user: User, db) -> Dict[str, Any]:
        """Validate relationship creation"""
        validated_data = data.model_dump()
        
        # Concepts existence is validated in service
        
        return validated_data
    
    async def validate_update(
        self,
        resource_id: str,
        updates: RelationshipUpdate,
        current_user: User,
        db
    ) -> Optional[Dict[str, Any]]:
        """Validate relationship update"""
        # Check if relationship exists
        relationship = await self.service.get_by_id(resource_id)
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found"
            )
        
        return None  # No modifications needed
    
    async def validate_delete(self, resource_id: str, current_user: User, db) -> Relationship:
        """Validate relationship deletion"""
        # Check if relationship exists
        relationship = await self.service.get_by_id(resource_id)
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relationship not found"
            )
        
        return relationship
    
    async def sync_from_github(self, github_token: str, current_user: User, **kwargs) -> List[Relationship]:
        """Sync relationships from GitHub (not implemented)"""
        return []
    
    # Override create to use service with ontological reasoning
    async def create(self, data: RelationshipCreate, current_user: User, db) -> Relationship:
        """
        Create a new relationship with automatic inverse creation
        
        When you create a relationship like "Car is_a Vehicle",
        the service automatically creates the inverse "Vehicle has_subclass Car"
        """
        try:
            validated_data = await self.validate_create(data, current_user, db)
            relationship = await self.service.create(validated_data)
            logger.info(
                f"Created relationship {relationship.id} with ontological reasoning "
                f"(inverse automatically created)"
            )
            return relationship
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Relationship creation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create relationship: {str(e)}"
            )
    
    # Additional methods
    
    async def get_by_metamodel(
        self,
        metamodel_id: str,
        skip: int = 0,
        limit: int = 100,
        include_inverse: bool = True
    ) -> List[Relationship]:
        """Get all relationships for a metamodel"""
        return await self.service.get_by_metamodel(metamodel_id, skip, limit, include_inverse)
    
    async def get_by_concept(
        self,
        concept_id: str,
        direction: str = "both"
    ) -> Dict[str, List[Relationship]]:
        """
        Get all relationships for a concept
        
        Args:
            concept_id: Concept ID
            direction: "outgoing", "incoming", or "both"
            
        Returns:
            Dict with "outgoing" and "incoming" relationship lists
        """
        if direction not in ["outgoing", "incoming", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Direction must be 'outgoing', 'incoming', or 'both'"
            )
        
        return await self.service.get_by_concept(concept_id, direction)
    
    async def get_by_type(
        self,
        metamodel_id: str,
        relationship_type: RelationshipType
    ) -> List[Relationship]:
        """Get all relationships of a specific type"""
        return await self.service.get_by_type(metamodel_id, relationship_type)
    
    async def infer_relationships(
        self,
        metamodel_id: str,
        current_user: User,
        db
    ) -> Dict[str, Any]:
        """
        Infer new relationships using ontological reasoning
        
        Applies transitivity rules:
        - If A is_a B and B is_a C, then A is_a C
        - If A part_of B and B part_of C, then A part_of C
        
        Returns:
            Dict with count and list of inferred relationships
        """
        try:
            inferred = await self.service.infer_relationships(metamodel_id)
            logger.info(f"Inferred {len(inferred)} relationships for metamodel {metamodel_id}")
            return {
                "count": len(inferred),
                "relationships": inferred,
                "message": f"Successfully inferred {len(inferred)} new relationships"
            }
        except Exception as e:
            logger.error(f"Relationship inference error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to infer relationships: {str(e)}"
            )
