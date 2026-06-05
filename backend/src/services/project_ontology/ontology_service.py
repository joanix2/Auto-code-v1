import logging
from typing import Any
from uuid import uuid4
from src.models.ontology import OntologyGraph
from src.repositories.project_ontology.ontology_repository import OntologyGraphRepository
from src.services.base_service import BaseService

logger = logging.getLogger(__name__)

class OntologyService(BaseService[OntologyGraph]):
    def __init__(self, repo: OntologyGraphRepository):
        self.repo = repo

    async def create(self, data: dict[str, Any]) -> OntologyGraph:
        data.setdefault("id", str(uuid4()))
        return await self.repo.create(data)

    async def get_by_id(self, entity_id: str) -> OntologyGraph | None:
        return await self.repo.get_by_id(entity_id)

    async def get_all(self, skip=0, limit=100, **kwargs) -> list[OntologyGraph]:
        return await self.repo.get_all(skip, limit)

    async def update(self, entity_id: str, update_data: dict[str, Any]) -> OntologyGraph | None:
        return await self.repo.update(entity_id, update_data)

    async def delete(self, entity_id: str) -> bool:
        return await self.repo.delete(entity_id)
