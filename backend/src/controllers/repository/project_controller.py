import logging
from fastapi import APIRouter, Depends, HTTPException, status

from src.controllers.base_controller import BaseController
from src.database import get_db
from src.models.repository.project import Project, ProjectCreate, ProjectUpdate
from src.models.oauth.user import User
from src.repositories.repository.project_repository import ProjectRepository
from src.services.repository.project_service import ProjectService
from src.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectController(BaseController[Project, ProjectCreate, ProjectUpdate]):
    def __init__(self, service: ProjectService):
        super().__init__(service)
        self.service = service

    async def validate_create(self, data: ProjectCreate, current_user: User, db) -> ProjectCreate:
        if not data.name or len(data.name.strip()) < 1:
            raise HTTPException(status_code=400, detail="Project name is required")
        return data

    async def validate_update(self, id: str, data: ProjectUpdate, current_user: User, db) -> ProjectUpdate:
        if data.name is not None and len(data.name.strip()) < 1:
            raise HTTPException(status_code=400, detail="Project name cannot be empty")
        return data

    async def create(self, data: ProjectCreate, current_user: User, db) -> Project:
        validated = await self.validate_create(data, current_user, db)
        return await self.service.create(validated.model_dump())

    async def get_by_id(self, resource_id: str, current_user: User, db) -> Project:
        project = await self.service.get_by_id(resource_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    async def get_all(self, current_user: User, db, skip: int = 0, limit: int = 100, **filters) -> list[Project]:
        return await self.service.get_all(skip, limit)

    async def update(self, id: str, data: ProjectUpdate, current_user: User, db) -> Project:
        validated = await self.validate_update(id, data, current_user, db)
        update_dict = validated.model_dump(exclude_unset=True)
        updated = await self.service.update(id, update_dict)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return updated

    async def delete(self, id: str, current_user: User, db) -> dict:
        deleted = await self.service.delete(id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return {"message": "Project deleted successfully"}


def get_controller(db=Depends(get_db)) -> ProjectController:
    project_repo = ProjectRepository(db)
    service = ProjectService(project_repo)
    return ProjectController(service)


@router.get("/", response_model=list[Project])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: ProjectController = Depends(get_controller),
):
    return await controller.get_all(current_user, db, skip, limit)


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: ProjectController = Depends(get_controller),
):
    return await controller.get_by_id(project_id, current_user, db)


@router.post("/", response_model=Project, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: ProjectController = Depends(get_controller),
):
    return await controller.create(project_data, current_user, db)


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    updates: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: ProjectController = Depends(get_controller),
):
    return await controller.update(project_id, updates, current_user, db)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
    controller: ProjectController = Depends(get_controller),
):
    return await controller.delete(project_id, current_user, db)
