"""
Repository repository - Data access layer for GitHub repositories
"""

import logging

from ...models.repository import Repository
from ..base import BaseRepository, convert_neo4j_types

logger = logging.getLogger(__name__)


class RepositoryRepository(BaseRepository[Repository]):
    """Repository for Repository entities"""

    def __init__(self, db):
        super().__init__(db, Repository, "Repository")

    async def get_by_github_id(self, github_id: int) -> Repository | None:
        """
        Get repository by GitHub ID

        Args:
            github_id: GitHub repository ID

        Returns:
            Repository or None if not found
        """
        query = """
        MATCH (n:Repository {github_id: $github_id})
        RETURN n
        """
        result = self.db.execute_query(query, {"github_id": github_id})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["n"]))

    async def get_by_full_name(self, full_name: str) -> Repository | None:
        """
        Get repository by full name (owner/repo)

        Args:
            full_name: Repository full name (e.g., "owner/repo")

        Returns:
            Repository or None if not found
        """
        query = """
        MATCH (n:Repository {full_name: $full_name})
        RETURN n
        """
        result = self.db.execute_query(query, {"full_name": full_name})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["n"]))

    async def get_by_owner(self, owner_username: str) -> list[Repository]:
        """
        Get all repositories for an owner, ordered by most recent commit

        Args:
            owner_username: Owner username

        Returns:
            List of repositories ordered by last commit date (most recent first)
        """
        query = """
        MATCH (n:Repository {owner_username: $owner_username})
        RETURN n
        ORDER BY n.github_pushed_at DESC
        """
        result = self.db.execute_query(query, {"owner_username": owner_username})
        return [self.model(**convert_neo4j_types(row["n"])) for row in result]
