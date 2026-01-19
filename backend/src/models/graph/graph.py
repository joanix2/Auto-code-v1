"""
Graph - Abstract base class for graph structures
"""
from abc import ABC, abstractmethod
from pydantic import Field
from typing import List, Dict, Any, Optional

from ..base import BaseEntity, BaseSemanticModel
from .node_type import NodeType
from .edge_type import EdgeType


class Graph(BaseEntity, BaseSemanticModel, ABC):
    """
    Abstract Graph - Represents a graph structure containing nodes and edges
    
    A graph is a container for nodes and edges.
    In the MDE context, a Metamodel is a graph containing:
    - Concept nodes
    - Attribute nodes
    - Relationship edges (connecting concepts)
    
    Graphs are stored as nodes in Neo4j with relationships to their contained nodes.
    
    Multiple inheritance:
    - BaseEntity: provides id, created_at, updated_at
    - BaseSemanticModel: provides name, description
    """
    
    # Metrics
    node_count: int = Field(default=0, ge=0, description="Total number of nodes in the graph")
    edge_count: int = Field(default=0, ge=0, description="Total number of edges in the graph")
    
    # Ownership
    owner_id: Optional[str] = Field(default=None, description="ID of the graph owner/creator")
    
    # Type constraints (M3 configuration)
    allowed_node_types: List[NodeType] = Field(default_factory=list, description="List of allowed node types in this graph")
    allowed_edge_types: List[EdgeType] = Field(default_factory=list, description="List of allowed edge types in this graph")
    
    @abstractmethod
    def get_graph_type(self) -> str:
        """
        Return the type of this graph (metamodel, knowledge_graph, etc.)
        Must be implemented by subclasses
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
            "allowed_node_types": [nt.model_dump() for nt in self.allowed_node_types],
            "allowed_edge_types": [et.model_dump() for et in self.allowed_edge_types],
            "metrics": self.get_metrics(),
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    class Config:
        from_attributes = True
