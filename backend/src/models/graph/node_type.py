"""
NodeType - M3 Base class for semantic node types
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import List

from backend.src.models.base import BaseSemanticModel, GenderType


class NodeType(BaseSemanticModel):
    """
    M3 NodeType - Defines a type of node in the metamodel
    
    This is a meta-class that defines what types of nodes can exist.
    Example: In a metamodel, we can have Concept, Attribute, Relation nodes.
    """
    label: str = Field(..., description="Display label (singular)")
    labelPlural: str = Field(..., description="Display label (plural)")
    gender: GenderType = Field(..., description="Grammatical gender for articles")
    article: str = Field(..., description="Definite article (le, la, l')")
    
    def get_article_maj(self) -> str:
        """Return article with capital letter"""
        return self.article.capitalize()
    
    class Config:
        use_enum_values = True
