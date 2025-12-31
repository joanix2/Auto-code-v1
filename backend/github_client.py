"""
GitHub API integration module.
Handles interactions with GitHub Issues and Pull Requests.
"""
import logging
from typing import Dict, Any, Optional
from github import Github, GithubException
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub API client for managing issues and pull requests"""
    
    def __init__(self):
        self.client = None
        self.repo = None
        self._initialize()
    
    def _initialize(self):
        """Initialize GitHub client and repository"""
        try:
            if not config.GITHUB_TOKEN:
                logger.warning("GitHub token not configured")
                return
                
            self.client = Github(config.GITHUB_TOKEN)
            repo_path = f"{config.GITHUB_OWNER}/{config.GITHUB_REPO}"
            self.repo = self.client.get_repo(repo_path)
            logger.info(f"Connected to GitHub repository: {repo_path}")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
    
    def create_issue(self, title: str, body: str, labels: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new issue in the repository
        
        Args:
            title: Issue title
            body: Issue description
            labels: Optional list of label names
            
        Returns:
            Dictionary with issue information or None if failed
        """
        try:
            if not self.repo:
                logger.error("GitHub repository not initialized")
                return None
            
            issue_labels = labels or []
            issue = self.repo.create_issue(
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
    
    def get_issue(self, issue_number: int) -> Optional[Dict[str, Any]]:
        """
        Get issue details
        
        Args:
            issue_number: Issue number
            
        Returns:
            Dictionary with issue information or None if failed
        """
        try:
            if not self.repo:
                logger.error("GitHub repository not initialized")
                return None
            
            issue = self.repo.get_issue(issue_number)
            
            return {
                "issue_number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "url": issue.html_url
            }
            
        except GithubException as e:
            logger.error(f"GitHub API error getting issue: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get issue: {e}")
            return None
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a pull request
        
        Args:
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch (default: main)
            
        Returns:
            Dictionary with PR information or None if failed
        """
        try:
            if not self.repo:
                logger.error("GitHub repository not initialized")
                return None
            
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch
            )
            
            result = {
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "title": pr.title,
                "state": pr.state
            }
            
            logger.info(f"Created PR #{pr.number}: {title}")
            return result
            
        except GithubException as e:
            logger.error(f"GitHub API error creating PR: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create PR: {e}")
            return None
    
    def update_issue(self, issue_number: int, state: str = None, comment: str = None) -> bool:
        """
        Update an issue
        
        Args:
            issue_number: Issue number
            state: New state ('open' or 'closed')
            comment: Comment to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.repo:
                logger.error("GitHub repository not initialized")
                return False
            
            issue = self.repo.get_issue(issue_number)
            
            if state:
                issue.edit(state=state)
            
            if comment:
                issue.create_comment(comment)
            
            logger.info(f"Updated issue #{issue_number}")
            return True
            
        except GithubException as e:
            logger.error(f"GitHub API error updating issue: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to update issue: {e}")
            return False


# Global instance
github_client = GitHubClient()
