"""
Controller pour la gestion des Individus
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from src.models.individu import Individu, IndividuCreate, IndividuUpdate
from src.repositories.individu_repository import IndividuRepository

router = APIRouter(prefix="/api/individus", tags=["individus"])


@router.post("/", response_model=Individu, status_code=status.HTTP_201_CREATED)
async def create_individu(individu: IndividuCreate):
    """Crée un nouvel individu"""
    try:
        return IndividuRepository.create(individu)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de l'individu: {str(e)}"
        )


@router.get("/{individu_id}", response_model=Individu)
async def get_individu(individu_id: str):
    """Récupère un individu par son ID"""
    individu = IndividuRepository.get_by_id(individu_id)
    if not individu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individu {individu_id} non trouvé"
        )
    return individu


@router.get("/project/{project_id}", response_model=List[Individu])
async def get_project_individus(project_id: str):
    """Récupère tous les individus d'un projet"""
    return IndividuRepository.get_by_project(project_id)


@router.get("/classe/{classe_id}", response_model=List[Individu])
async def get_classe_individus(classe_id: str):
    """Récupère tous les individus d'une classe"""
    return IndividuRepository.get_by_classe(classe_id)


@router.put("/{individu_id}", response_model=Individu)
async def update_individu(individu_id: str, individu: IndividuUpdate):
    """Met à jour un individu"""
    updated_individu = IndividuRepository.update(individu_id, individu)
    if not updated_individu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individu {individu_id} non trouvé"
        )
    return updated_individu


@router.delete("/{individu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_individu(individu_id: str):
    """Supprime un individu"""
    success = IndividuRepository.delete(individu_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Individu {individu_id} non trouvé"
        )
