"""
Controller pour la gestion des Projects
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from src.models.project import Project, ProjectCreate, ProjectUpdate
from src.repositories.project_repository import ProjectRepository

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate):
    """Crée un nouveau projet"""
    try:
        return ProjectRepository.create(project)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du projet: {str(e)}"
        )


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Récupère un projet par son ID"""
    project = ProjectRepository.get_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    return project


@router.get("/user/{user_id}", response_model=List[Project])
async def get_user_projects(user_id: str, skip: int = 0, limit: int = 100):
    """Récupère tous les projets d'un utilisateur"""
    return ProjectRepository.get_by_user(user_id, skip, limit)


@router.get("/user/{user_id}/search", response_model=List[Project])
async def search_projects(user_id: str, q: str, threshold: float = 0.6):
    """
    Recherche des projets par nom avec distance de Levenshtein
    - q: terme de recherche
    - threshold: seuil de similarité minimum (0.0 à 1.0, par défaut 0.6)
    """
    if not q or len(q.strip()) == 0:
        return []
    
    # Valider le threshold
    if threshold < 0.0 or threshold > 1.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le threshold doit être entre 0.0 et 1.0"
        )
    
    return ProjectRepository.search_by_name(user_id, q.strip(), threshold)


@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, project: ProjectUpdate):
    """Met à jour un projet"""
    updated_project = ProjectRepository.update(project_id, project)
    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
    return updated_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str):
    """Supprime un projet"""
    success = ProjectRepository.delete(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projet {project_id} non trouvé"
        )
