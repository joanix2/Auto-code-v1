"""
Controller pour la gestion des Classes
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from src.models.classe import Classe, ClasseCreate, ClasseUpdate
from src.repositories.classe_repository import ClasseRepository

router = APIRouter(prefix="/api/classes", tags=["classes"])


@router.post("/", response_model=Classe, status_code=status.HTTP_201_CREATED)
async def create_classe(classe: ClasseCreate):
    """Crée une nouvelle classe"""
    try:
        return ClasseRepository.create(classe)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la classe: {str(e)}"
        )


@router.get("/{classe_id}", response_model=Classe)
async def get_classe(classe_id: str):
    """Récupère une classe par son ID"""
    classe = ClasseRepository.get_by_id(classe_id)
    if not classe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classe {classe_id} non trouvée"
        )
    return classe


@router.get("/project/{project_id}", response_model=List[Classe])
async def get_project_classes(project_id: str):
    """Récupère toutes les classes d'un projet"""
    return ClasseRepository.get_by_project(project_id)


@router.put("/{classe_id}", response_model=Classe)
async def update_classe(classe_id: str, classe: ClasseUpdate):
    """Met à jour une classe"""
    updated_classe = ClasseRepository.update(classe_id, classe)
    if not updated_classe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classe {classe_id} non trouvée"
        )
    return updated_classe


@router.delete("/{classe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_classe(classe_id: str):
    """Supprime une classe"""
    success = ClasseRepository.delete(classe_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classe {classe_id} non trouvée"
        )
