"""
Edge - Abstract base class for graph edges
"""
from abc import ABC, abstractmethod
from pydantic import Field
from typing import Optional, Dict, Any

from ..base import BaseEntity, BaseSemanticModel


class Edge(BaseEntity, BaseSemanticModel, ABC):
    """
    Abstract Edge - Represents a relationship/connection between two nodes in a graph
    
    Edges connect nodes and are stored as relationships in Neo4j.
    In the MDE context, Relationship entities are edges between Concept nodes.
    
    Multiple inheritance:
    - BaseEntity: provides id, created_at, updated_at
    - BaseSemanticModel: provides name, description
    """
     
    # Graph metadata
    graph_id: str = Field(..., description="ID of the parent graph (metamodel)")
    edge_type: str = Field(..., description="Type of this edge")

    # Source and target nodes
    source_id: str = Field(..., description="ID of the source node")
    target_id: str = Field(..., description="ID of the target node")
    
    # Optional labels
    source_label: Optional[str] = Field(default=None, description="Label of source node (cached)")
    target_label: Optional[str] = Field(default=None, description="Label of target node (cached)")
    
    @abstractmethod
    def get_edge_type(self) -> str:
        """
        Return the type of this edge (is_a, has_part, etc.)
        Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    def get_display_label(self) -> str:
        """
        Return the label to display on the edge in graph visualizations
        Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    def is_directed(self) -> bool:
        """
        Return True if this edge is directed (has a specific direction)
        Return False for undirected edges
        """
        pass
    
    def get_endpoints(self) -> tuple[str, str]:
        """Get the (source_id, target_id) endpoints of this edge"""
        return (self.source_id, self.target_id)
    
    def reverse(self) -> tuple[str, str]:
        """Get the reverse direction (target_id, source_id)"""
        return (self.target_id, self.source_id)
    
    def to_graph_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary suitable for graph visualization
        Override in subclasses to add specific properties
        """
        display_label = self.get_display_label()
        return {
            "id": self.id,
            "description": self.description,
            "type": display_label,  # Use uppercase display label for consistency
            "label": display_label,  # Same for label
            "source": self.source_id,
            "target": self.target_id,
            "source_label": self.source_label,
            "target_label": self.target_label,
            "directed": self.is_directed(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    class Config:
        from_attributes = True
