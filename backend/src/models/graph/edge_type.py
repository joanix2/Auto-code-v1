"""
EdgeType - M3 Base class for semantic edge types
"""
from pydantic import Field
from typing import List
from backend.src.models.base import BaseSemanticModel


class EdgeType(BaseSemanticModel):
    """
    M3 EdgeType - Defines a type of edge in the metamodel
    
    This is a meta-class that defines what types of edges can exist
    and which node types they can connect.
    
    Example: DOMAIN edge connects RELATION to CONCEPT
    """
    
    sourceNodeTypes: List[str] = Field(..., description="IDs of valid source node types")
    targetNodeTypes: List[str] = Field(..., description="IDs of valid target node types")
    directed: bool = Field(default=True, description="Whether the edge is directed")
    
    def allows_connection(self, source_type_id: str, target_type_id: str) -> bool:
        """
        Check if this edge type allows a connection between the given node types
        
        Args:
            source_type_id: ID of the source node type
            target_type_id: ID of the target node type
            
        Returns:
            True if the connection is allowed, False otherwise
        """
        return (source_type_id in self.sourceNodeTypes and 
                target_type_id in self.targetNodeTypes)
