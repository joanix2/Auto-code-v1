from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# Enums
MetamodelStatus = Literal["draft", "validated", "deprecated"]


# Base Model
class MetamodelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    version: str = Field(..., min_length=1, max_length=50)
    concepts: int = Field(default=0, ge=0)
    relations: int = Field(default=0, ge=0)
    author: Optional[str] = None
    status: MetamodelStatus = "draft"


# Create Model
class MetamodelCreate(MetamodelBase):
    pass


# Update Model
class MetamodelUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    concepts: Optional[int] = Field(None, ge=0)
    relations: Optional[int] = Field(None, ge=0)
    author: Optional[str] = None
    status: Optional[MetamodelStatus] = None


# Response Model
class Metamodel(MetamodelBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
