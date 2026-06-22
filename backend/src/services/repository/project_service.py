import logging
from typing import Any
from uuid import uuid4

from src.models.repository.project import Project
from src.repositories.repository.project_repository import ProjectRepository
from src.services.base_service import BaseService

logger = logging.getLogger(__name__)


class ProjectService(BaseService[Project]):
    def __init__(self, project_repo: ProjectRepository):
        self.project_repo = project_repo

    async def create(self, data: dict[str, Any]) -> Project:
        project_data = {**data}
        project_data["id"] = str(uuid4())
        project_data.setdefault("status", "draft")
        project_data.setdefault("description", "")
        project = await self.project_repo.create(project_data)
        logger.info(f"Created project: {project.name}")
        return project

    async def get_by_id(self, project_id: str) -> Project | None:
        return await self.project_repo.get_by_id(project_id)

    async def get_all(self, skip: int = 0, limit: int = 100, **kwargs) -> list[Project]:
        return await self.project_repo.get_all(skip, limit)

    async def update(self, project_id: str, update_data: dict[str, Any]) -> Project | None:
        updates = {k: v for k, v in update_data.items() if v is not None}
        if not updates:
            return await self.get_by_id(project_id)
        return await self.project_repo.update(project_id, updates)

    async def delete(self, project_id: str) -> bool:
        deleted = await self.project_repo.delete(project_id)
        if deleted:
            logger.info(f"Deleted project: {project_id}")
        return deleted
