"""
GitHub Sync Service - Synchronize repositories and issues from GitHub
"""
from typing import List
from github import Github
import uuid
import logging

from ...models.repository import Repository, RepositoryCreate
from ...models.issue import Issue, IssueCreate
from ...repositories.repository_repository import RepositoryRepository
from ...repositories.issue_repository import IssueRepository

logger = logging.getLogger(__name__)


class GitHubSyncService:
    """Service for syncing with GitHub"""

    def __init__(
        self, 
        github_token: str, 
        repo_repository: RepositoryRepository, 
        issue_repository: IssueRepository
    ):
        self.github = Github(github_token)
        self.repo_repository = repo_repository
        self.issue_repository = issue_repository

    async def sync_user_repositories(self, username: str) -> List[Repository]:
        """
        Sync all repositories for a user
        
        Args:
            username: GitHub username
            
        Returns:
            List of synced repositories
        """
        logger.info(f"Syncing repositories for {username}")

        gh_user = self.github.get_user(username)
        repos = []

        for gh_repo in gh_user.get_repos():
            repo_data = {
                "id": f"repo-{uuid.uuid4()}",
                "name": gh_repo.name,
                "full_name": gh_repo.full_name,
                "owner_username": username,
                "description": gh_repo.description,
                "github_id": gh_repo.id,
                "default_branch": gh_repo.default_branch or "main",
                "is_private": gh_repo.private,
                "open_issues_count": gh_repo.open_issues_count
            }

            # Upsert: create or update
            existing = await self.repo_repository.get_by_github_id(gh_repo.id)
            if existing:
                repo = await self.repo_repository.update(existing.id, repo_data)
            else:
                repo = await self.repo_repository.create(repo_data)

            repos.append(repo)

        logger.info(f"Synced {len(repos)} repositories")
        return repos

    async def sync_repository_issues(self, repository_id: str, username: str) -> List[Issue]:
        """
        Sync all issues for a repository
        
        Args:
            repository_id: Repository ID
            username: GitHub username (for author)
            
        Returns:
            List of synced issues
        """
        repo = await self.repo_repository.get_by_id(repository_id)
        if not repo:
            raise ValueError(f"Repository {repository_id} not found")

        logger.info(f"Syncing issues for {repo.full_name}")

        gh_repo = self.github.get_repo(repo.full_name)
        issues = []

        for gh_issue in gh_repo.get_issues(state="all"):
            # Skip PRs (they have pull_request attribute)
            if gh_issue.pull_request:
                continue

            # Determine status based on GitHub state
            if gh_issue.state == "closed":
                status = "closed"
            else:
                status = "open"

            issue_data = {
                "id": f"issue-{uuid.uuid4()}",
                "title": gh_issue.title,
                "description": gh_issue.body or "",
                "repository_id": repository_id,
                "author_username": username,
                "github_issue_number": gh_issue.number,
                "github_issue_url": gh_issue.html_url,
                "status": status,
                "priority": "medium",
                "issue_type": "feature"
            }

            # Upsert
            existing = await self.issue_repository.get_by_github_issue_number(
                repository_id, 
                gh_issue.number
            )
            if existing:
                issue = await self.issue_repository.update(existing.id, issue_data)
            else:
                issue = await self.issue_repository.create(issue_data)

            issues.append(issue)

        logger.info(f"Synced {len(issues)} issues")
        return issues
