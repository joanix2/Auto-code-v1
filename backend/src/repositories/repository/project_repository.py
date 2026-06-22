import logging

from ...models.repository.project import Project
from ..base import BaseRepository

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db):
        super().__init__(db, Project, "Project")
