import logging
from ...models.repository.project import Project
from ..base import BaseRepository, convert_neo4j_types

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db):
        super().__init__(db, Project, "Project")
