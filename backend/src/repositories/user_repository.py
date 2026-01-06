"""
User repository - Data access layer for users
"""
from typing import Optional
from .base import BaseRepository, convert_neo4j_types
from ..models.user import User
import logging

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User entities"""

    def __init__(self, db):
        super().__init__(db, User, "User")

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            username: Username to search for
            
        Returns:
            User or None if not found
        """
        query = """
        MATCH (n:User {username: $username})
        RETURN n
        """
        result = self.db.execute_query(query, {"username": username})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["n"]))

    async def get_by_github_id(self, github_id: int) -> Optional[User]:
        """
        Get user by GitHub ID
        
        Args:
            github_id: GitHub user ID
            
        Returns:
            User or None if not found
        """
        query = """
        MATCH (n:User {github_id: $github_id})
        RETURN n
        """
        result = self.db.execute_query(query, {"github_id": github_id})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["n"]))

    async def update_github_token(self, user_id: str, github_token: str) -> Optional[User]:
        """
        Update user's GitHub token
        
        Args:
            user_id: User ID
            github_token: New GitHub access token
            
        Returns:
            Updated user or None if not found
        """
        return await self.update(user_id, {"github_token": github_token})
