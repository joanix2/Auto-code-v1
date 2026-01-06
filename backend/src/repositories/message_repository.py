"""
Message repository - Data access layer for PR comments
"""
from typing import Optional, List
from .base import BaseRepository
from ..models.message import Message
import logging

logger = logging.getLogger(__name__)


class MessageRepository(BaseRepository[Message]):
    """Repository for Message entities (PR comments)"""

    def __init__(self, db):
        super().__init__(db, Message, "Message")

    async def get_by_issue(self, issue_id: str) -> List[Message]:
        """
        Get all messages for an issue
        
        Args:
            issue_id: Issue ID
            
        Returns:
            List of messages ordered by creation date
        """
        query = """
        MATCH (n:Message {issue_id: $issue_id})
        RETURN n
        ORDER BY n.created_at ASC
        """
        result = await self.db.execute_query(query, {"issue_id": issue_id})
        return [self.model(**row["n"]) for row in result]

    async def get_by_github_comment_id(self, github_comment_id: int) -> Optional[Message]:
        """
        Get message by GitHub comment ID
        
        Args:
            github_comment_id: GitHub comment ID
            
        Returns:
            Message or None if not found
        """
        query = """
        MATCH (n:Message {github_comment_id: $github_comment_id})
        RETURN n
        """
        result = await self.db.execute_query(query, {"github_comment_id": github_comment_id})
        if not result:
            return None
        return self.model(**result[0]["n"])

    async def get_copilot_messages(self, issue_id: str) -> List[Message]:
        """
        Get all Copilot messages for an issue
        
        Args:
            issue_id: Issue ID
            
        Returns:
            List of Copilot messages
        """
        query = """
        MATCH (n:Message {issue_id: $issue_id, author_type: "copilot"})
        RETURN n
        ORDER BY n.created_at ASC
        """
        result = await self.db.execute_query(query, {"issue_id": issue_id})
        return [self.model(**row["n"]) for row in result]
