"""
Graph - Abstract base class for graph structures
"""
from abc import ABC, abstractmethod
from pydantic import Field
from typing import List, Dict, Any, Optional

from ..base import BaseSemanticModel


class Graph(BaseSemanticModel, ABC):
    """
    Abstract Graph - Represents a graph structure containing nodes and edges
    
    A graph is a container for nodes and edges.
    In the MDE context, a Metamodel is a graph containing:
    - Concept nodes
    - Attribute nodes
    - Relationship edges (connecting concepts)
    
    Graphs are stored as nodes in Neo4j with relationships to their contained nodes.
    """
    
    # Metrics
    node_count: int = Field(default=0, ge=0, description="Total number of nodes in the graph")
    edge_count: int = Field(default=0, ge=0, description="Total number of edges in the graph")
    
    # Ownership
    owner_id: Optional[str] = Field(default=None, description="ID of the graph owner/creator")
    
    @abstractmethod
    def get_graph_type(self) -> str:
        """
        Return the type of this graph (metamodel, knowledge_graph, etc.)
        Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    def get_node_types(self) -> List[str]:
        """
        Return the list of node types that can exist in this graph
        Example: ["concept", "attribute"] for a metamodel
        """
        pass
    
    @abstractmethod
    def get_edge_types(self) -> List[str]:
        """
        Return the list of edge types that can exist in this graph
        Example: ["is_a", "has_part", "has_subclass", "part_of"] for a metamodel
        """
        pass
    
    def increment_node_count(self) -> None:
        """Increment the node count"""
        self.node_count += 1
    
    def decrement_node_count(self) -> None:
        """Decrement the node count"""
        if self.node_count > 0:
            self.node_count -= 1
    
    def increment_edge_count(self) -> None:
        """Increment the edge count"""
        self.edge_count += 1
    
    def decrement_edge_count(self) -> None:
        """Decrement the edge count"""
        if self.edge_count > 0:
            self.edge_count -= 1
    
    def get_metrics(self) -> Dict[str, int]:
        """Get graph metrics"""
        return {
            "nodes": self.node_count,
            "edges": self.edge_count,
        }
    
    def to_graph_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary suitable for graph visualization
        Override in subclasses to add specific properties
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.get_graph_type(),
            "node_types": self.get_node_types(),
            "edge_types": self.get_edge_types(),
            "metrics": self.get_metrics(),
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    class Config:
        from_attributes = True
