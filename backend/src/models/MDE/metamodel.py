"""
Metamodel Model - Container for concepts and relationships (MDE ontology)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

from ..graph import Graph


# Enums - Keep Literal for backward compatibility
MetamodelStatus = Literal["draft", "validated", "deprecated"]


class Metamodel(Graph):
    """
    Metamodel - A graph containing concepts and relationships
    
    A metamodel defines:
    - The structure of a domain (concepts/classes as nodes)
    - The relationships between concepts (as edges)
    - Constraints and rules
    - Can be used to generate code, validate models, etc.
    
    Inherits from Graph:
    - name, description (from Graph)
    - node_count, edge_count (from Graph)
    - owner_id (from Graph)
    """
    version: str = Field(..., min_length=1, max_length=50, description="Metamodel version")
    status: MetamodelStatus = Field(default="draft", description="Metamodel status")
    repository_id: Optional[str] = Field(default=None, description="GitHub repository ID")
    
    # Backward compatibility - map to Graph properties
    @property
    def author(self) -> Optional[str]:
        """Alias for owner_id (backward compatibility)"""
        return self.owner_id
    
    @author.setter
    def author(self, value: Optional[str]):
        """Setter for author (backward compatibility)"""
        self.owner_id = value
    
    @property
    def concepts(self) -> int:
        """Alias for node_count (backward compatibility)"""
        return self.node_count
    
    @concepts.setter
    def concepts(self, value: int):
        """Setter for concepts (backward compatibility)"""
        self.node_count = value
    
    @property
    def relations(self) -> int:
        """Alias for edge_count (backward compatibility)"""
        return self.edge_count
    
    @relations.setter
    def relations(self, value: int):
        """Setter for relations (backward compatibility)"""
        self.edge_count = value
    
    # Abstract methods implementation
    def get_graph_type(self) -> str:
        """Return 'metamodel' as the graph type"""
        return "metamodel"
    
    def get_node_types(self) -> List[str]:
        """Return the types of nodes in a metamodel"""
        return ["concept", "attribute"]
    
    def get_edge_types(self) -> List[str]:
        """Return the types of edges in a metamodel"""
        return ["is_a", "has_subclass", "has_part", "part_of", "has_attribute"]
    
    class Config:
        from_attributes = True


# Base Model for Create/Update operations
class MetamodelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    version: str = Field(..., min_length=1, max_length=50)
    node_count: int = Field(default=0, ge=0, description="Number of concepts")
    edge_count: int = Field(default=0, ge=0, description="Number of relationships")
    
    # Backward compatibility aliases
    @property
    def concepts(self) -> int:
        """Alias for node_count (backward compatibility)"""
        return self.node_count
    
    @property
    def relations(self) -> int:
        """Alias for edge_count (backward compatibility)"""
        return self.edge_count
    
    author: Optional[str] = None
    status: MetamodelStatus = "draft"


# Create Model
class MetamodelCreate(MetamodelBase):
    type: Optional[str] = "custom"
    documentation: Optional[str] = None
    namespace: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False
    repository_id: Optional[str] = None
    repository_path: Optional[str] = None


# Update Model
class MetamodelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    node_count: Optional[int] = Field(None, ge=0, description="Number of concepts")
    edge_count: Optional[int] = Field(None, ge=0, description="Number of relationships")
    
    # Backward compatibility - accept old field names
    concepts: Optional[int] = Field(None, ge=0, deprecated=True)
    relations: Optional[int] = Field(None, ge=0, deprecated=True)
    
    author: Optional[str] = None
    status: Optional[MetamodelStatus] = None
    type: Optional[str] = None
    documentation: Optional[str] = None
    namespace: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    collaborators: Optional[List[str]] = None
    is_public: Optional[bool] = None
    repository_path: Optional[str] = None


class MetamodelResponse(Metamodel):
    """Schema for metamodel response - includes all Metamodel fields"""
    pass


class MetamodelWithDetails(Metamodel):
    """Extended metamodel response with concepts and relationships"""
    concept_list: List[Dict[str, Any]] = Field(default_factory=list, description="List of concept details")
    relationship_list: List[Dict[str, Any]] = Field(default_factory=list, description="List of relationship details")
    
    class Config:
        from_attributes = True

