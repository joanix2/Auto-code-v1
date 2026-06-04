import logging
from typing import Any
from uuid import uuid4
from src.models.architecture import ArchitectureGraph, ArchitectureNode, ArchitectureEdge
from src.repositories.architecture.architecture_repository import ArchitectureGraphRepository as ArchitectureRepository
from src.services.base_service import BaseService
logger = logging.getLogger(__name__)
class ArchitectureService(BaseService[ArchitectureGraph]):
    def __init__(self, repo):
        self.repo = repo
    async def create(self, data: dict[str, Any]) -> ArchitectureGraph:
        data.setdefault("id", str(uuid4()))
        return await self.repo.create(data)
    async def get_by_id(self, entity_id: str) -> ArchitectureGraph | None:
        return await self.repo.get_by_id(entity_id)
    async def get_all(self, skip=0, limit=100, **kwargs) -> list[ArchitectureGraph]:
        return await self.repo.get_all(skip, limit)
    async def update(self, entity_id: str, update_data: dict[str, Any]) -> ArchitectureGraph | None:
        return await self.repo.update(entity_id, update_data)
    async def delete(self, entity_id: str) -> bool:
        return await self.repo.delete(entity_id)
