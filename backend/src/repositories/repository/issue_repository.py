"""
Issue repository - Data access layer for GitHub issues
"""
from typing import Optional, List
from ..base import BaseRepository, convert_neo4j_types
from ...models.repository.issue import Issue
import logging

logger = logging.getLogger(__name__)


class IssueRepository(BaseRepository[Issue]):
    """Repository for Issue entities"""

    def __init__(self, db):
        super().__init__(db, Issue, "Issue")

    async def get_by_repository(self, repository_id: str, status: Optional[str] = None) -> List[Issue]:
        """
        Get all issues for a repository
        
        Args:
            repository_id: Repository ID
            status: Optional status filter
            
        Returns:
            List of issues
        """
        where_clause = "WHERE n.repository_id = $repository_id"
        params = {"repository_id": repository_id}
        
        if status:
            where_clause += " AND n.status = $status"
            params["status"] = status

        query = f"""
        MATCH (n:Issue)
        {where_clause}
        RETURN n
        ORDER BY n.created_at DESC
        """
        
        result = self.db.execute_query(query, params)
        return [self.model(**convert_neo4j_types(row["n"])) for row in result]

    async def get_by_github_id(self, github_id: int) -> Optional[Issue]:
        """
        Get issue by GitHub ID
        
        Args:
            github_id: GitHub issue ID
            
        Returns:
            Issue or None if not found
        """
        query = """
        MATCH (n:Issue {github_id: $github_id})
        RETURN n
        """
        result = self.db.execute_query(query, {"github_id": github_id})
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["n"]))

    async def get_by_github_issue_number(self, repository_id: str, issue_number: int) -> Optional[Issue]:
        """
        Get issue by GitHub issue number
        
        Args:
            repository_id: Repository ID
            issue_number: GitHub issue number
            
        Returns:
            Issue or None if not found
        """
        query = """
        MATCH (n:Issue {repository_id: $repository_id, github_issue_number: $issue_number})
        RETURN n
        """
        result = self.db.execute_query(query, {
            "repository_id": repository_id,
            "issue_number": issue_number
        })
        if not result:
            return None
        return self.model(**convert_neo4j_types(result[0]["n"]))

    async def link_to_github(self, issue_id: str, github_data: dict) -> Optional[Issue]:
        """
        Link issue to GitHub issue/PR
        
        Args:
            issue_id: Issue ID
            github_data: GitHub data (issue_number, issue_url, pr_number, pr_url, branch_name)
            
        Returns:
            Updated issue or None if not found
        """
        return await self.update(issue_id, github_data)

    async def assign_to_copilot(self, issue_id: str, assigned: bool = True) -> Optional[Issue]:
        """
        Assign or unassign issue to/from Copilot
        
        Args:
            issue_id: Issue ID
            assigned: True to assign, False to unassign
            
        Returns:
            Updated issue or None if not found
        """
        from datetime import datetime
        
        if assigned:
            return await self.update(issue_id, {
                "assigned_to_copilot": True,
                "copilot_started_at": datetime.utcnow(),
                "status": "in_progress"
            })
        else:
            return await self.update(issue_id, {
                "assigned_to_copilot": False,
                "copilot_started_at": None
            })

    async def get_copilot_issues(self, repository_id: Optional[str] = None) -> List[Issue]:
        """
        Get all issues assigned to Copilot
        
        Args:
            repository_id: Optional repository ID filter
            
        Returns:
            List of issues assigned to Copilot
        """
        where_clause = "WHERE n.assigned_to_copilot = true"
        params = {}
        
        if repository_id:
            where_clause += " AND n.repository_id = $repository_id"
            params["repository_id"] = repository_id

        query = f"""
        MATCH (n:Issue)
        {where_clause}
        RETURN n
        ORDER BY n.copilot_started_at DESC
        """
        
        result = self.db.execute_query(query, params)
        return [self.model(**convert_neo4j_types(row["n"])) for row in result]
