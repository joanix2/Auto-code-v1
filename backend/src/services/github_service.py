"""GitHub Service - Interact with GitHub API"""
import httpx
from typing import Optional, Dict, List
from github import Github, GithubException
import logging

logger = logging.getLogger(__name__)


class GitHubService:
    """Service to interact with GitHub API"""
    
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        # PyGithub client for advanced operations
        self.client = Github(token) if token else None
    
    async def get_authenticated_user(self) -> Optional[Dict]:
        """Get authenticated user info from GitHub"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/user",
                    headers=self.headers,
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            logger.error(f"Error getting GitHub user: {e}")
            return None
    
    async def get_user_repositories(self, username: str = None, per_page: int = 100) -> List[Dict]:
        """Get user repositories from GitHub"""
        try:
            endpoint = f"{self.base_url}/user/repos" if not username else f"{self.base_url}/users/{username}/repos"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=self.headers,
                    params={"sort": "updated", "per_page": per_page},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return response.json()
                return []
        except Exception as e:
            logger.error(f"Error getting GitHub repositories: {e}")
            return []
    
    def create_issue(self, repo_full_name: str, title: str, body: str, labels: Optional[list] = None) -> Optional[Dict]:
        """Create a new issue in the repository"""
        try:
            if not self.client:
                logger.error("GitHub client not initialized")
                return None
            
            repo = self.client.get_repo(repo_full_name)
            issue_labels = labels or []
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=issue_labels
            )
            
            result = {
                "issue_number": issue.number,
                "issue_url": issue.html_url,
                "title": issue.title,
                "state": issue.state
            }
            
            logger.info(f"Created issue #{issue.number}: {title}")
            return result
            
        except GithubException as e:
            logger.error(f"GitHub API error creating issue: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            return None
    
    def update_issue(self, repo_full_name: str, issue_number: int, comment: str = None, state: str = None) -> bool:
        """Update an issue with a comment or state change"""
        try:
            if not self.client:
                logger.error("GitHub client not initialized")
                return False
            
            repo = self.client.get_repo(repo_full_name)
            issue = repo.get_issue(issue_number)
            
            if comment:
                issue.create_comment(comment)
                logger.info(f"Added comment to issue #{issue_number}")
            
            if state:
                issue.edit(state=state)
                logger.info(f"Changed issue #{issue_number} state to {state}")
            
            return True
            
        except GithubException as e:
            logger.error(f"GitHub API error updating issue: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update issue: {e}")
            return False
