"""
Node - Abstract base class for graph nodes
"""
from abc import ABC, abstractmethod
from pydantic import Field
from typing import Optional, Dict, Any

from ..base import BaseEntity


class Node(BaseEntity, ABC):
    """
    Abstract Node - Represents a vertex in a graph
    
    All nodes in a graph (Concept, Attribute, Relationship) inherit from this class.
    Nodes are stored as nodes in Neo4j.
    """
    
    # Core properties
    name: str = Field(..., min_length=1, max_length=200, description="Node name")
    description: Optional[str] = Field(default=None, description="Node description")
    
    # Position for graph visualization
    x_position: Optional[float] = Field(default=None, description="X coordinate in graph visualization")
    y_position: Optional[float] = Field(default=None, description="Y coordinate in graph visualization")
    
    # Graph metadata
    graph_id: str = Field(..., description="ID of the parent graph (metamodel)")
    
    @abstractmethod
    def get_node_type(self) -> str:
        """
        Return the type of this node (concept, attribute, relationship, etc.)
        Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    def get_display_label(self) -> str:
        """
        Return the label to display in graph visualizations
        Must be implemented by subclasses
        """
        pass
    
    def get_position(self) -> tuple[Optional[float], Optional[float]]:
        """Get the (x, y) position of this node"""
        return (self.x_position, self.y_position)
    
    def set_position(self, x: float, y: float) -> None:
        """Set the position of this node"""
        self.x_position = x
        self.y_position = y
    
    def to_graph_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary suitable for graph visualization
        Override in subclasses to add specific properties
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.get_node_type(),
            "label": self.get_display_label(),
            "x": self.x_position,
            "y": self.y_position,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    class Config:
        from_attributes = True
