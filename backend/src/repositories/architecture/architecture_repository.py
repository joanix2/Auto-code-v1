import logging
from ...models.architecture import ArchitectureGraph, ArchitectureNode, ArchitectureEdge
from ..base import BaseRepository, convert_neo4j_types
logger = logging.getLogger(__name__)
class ArchitectureGraphRepository(BaseRepository[ArchitectureGraph]):
    def __init__(self, db):
        super().__init__(db, ArchitectureGraph, "ArchitectureGraph")
class ArchitectureNodeRepository(BaseRepository[ArchitectureNode]):
    def __init__(self, db):
        super().__init__(db, ArchitectureNode, "ArchitectureNode")
class ArchitectureEdgeRepository(BaseRepository[ArchitectureEdge]):
    def __init__(self, db):
        super().__init__(db, ArchitectureEdge, "ArchitectureEdge")
