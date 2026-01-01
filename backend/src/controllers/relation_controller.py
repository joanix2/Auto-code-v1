"""
Controller pour la gestion des Relations
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from src.models.relation import (
    Relation, RelationCreate, RelationUpdate,
    RelationType, RelationTypeCreate, RelationTypeUpdate
)
from src.repositories.relation_repository import RelationRepository, RelationTypeRepository

router = APIRouter(prefix="/api/relations", tags=["relations"])


# Routes pour les types de relations
@router.post("/types", response_model=RelationType, status_code=status.HTTP_201_CREATED)
async def create_relation_type(relation_type: RelationTypeCreate):
    """Crée un nouveau type de relation"""
    try:
        return RelationTypeRepository.create(relation_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du type de relation: {str(e)}"
        )


@router.get("/types/{type_id}", response_model=RelationType)
async def get_relation_type(type_id: str):
    """Récupère un type de relation par son ID"""
    relation_type = RelationTypeRepository.get_by_id(type_id)
    if not relation_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type de relation {type_id} non trouvé"
        )
    return relation_type


@router.get("/types/project/{project_id}", response_model=List[RelationType])
async def get_project_relation_types(project_id: str):
    """Récupère tous les types de relations d'un projet"""
    return RelationTypeRepository.get_by_project(project_id)


@router.put("/types/{type_id}", response_model=RelationType)
async def update_relation_type(type_id: str, relation_type: RelationTypeUpdate):
    """Met à jour un type de relation"""
    updated_type = RelationTypeRepository.update(type_id, relation_type)
    if not updated_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type de relation {type_id} non trouvé"
        )
    return updated_type


@router.delete("/types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation_type(type_id: str):
    """Supprime un type de relation"""
    success = RelationTypeRepository.delete(type_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Type de relation {type_id} non trouvé"
        )


# Routes pour les relations
@router.post("/", response_model=Relation, status_code=status.HTTP_201_CREATED)
async def create_relation(relation: RelationCreate):
    """Crée une nouvelle relation"""
    try:
        return RelationRepository.create(relation)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la relation: {str(e)}"
        )


@router.get("/{relation_id}", response_model=Relation)
async def get_relation(relation_id: str):
    """Récupère une relation par son ID"""
    relation = RelationRepository.get_by_id(relation_id)
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relation {relation_id} non trouvée"
        )
    return relation


@router.get("/project/{project_id}", response_model=List[Relation])
async def get_project_relations(project_id: str):
    """Récupère toutes les relations d'un projet"""
    return RelationRepository.get_by_project(project_id)


@router.get("/individu/{individu_id}", response_model=List[Relation])
async def get_individu_relations(individu_id: str):
    """Récupère toutes les relations d'un individu"""
    return RelationRepository.get_by_individu(individu_id)


@router.put("/{relation_id}", response_model=Relation)
async def update_relation(relation_id: str, relation: RelationUpdate):
    """Met à jour une relation"""
    updated_relation = RelationRepository.update(relation_id, relation)
    if not updated_relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relation {relation_id} non trouvée"
        )
    return updated_relation


@router.delete("/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(relation_id: str):
    """Supprime une relation"""
    success = RelationRepository.delete(relation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Relation {relation_id} non trouvée"
        )
