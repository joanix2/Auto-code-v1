"""
Pull Request Service
Manages Pull Request operations via GitHub API
"""

import logging
from typing import Optional, Dict, Any, List
from github import Github, GithubException

logger = logging.getLogger(__name__)


class PullRequestService:
    """Service for managing Pull Requests on GitHub"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize PR service
        
        Args:
            token: GitHub personal access token
        """
        if not token:
            raise ValueError("GitHub token is required for Pull Request operations")
        
        self.github = Github(token)
        self.token = token
    
    def create_pull_request(
        self,
        repo_full_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False
    ) -> Dict[str, Any]:
        """
        Create a Pull Request
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch (default: main)
            draft: Create as draft PR
            
        Returns:
            dict with PR information:
            {
                "success": bool,
                "pr_number": int,
                "pr_url": str,
                "message": str
            }
        """
        try:
            logger.info(f"Creating PR for {repo_full_name}: {head_branch} -> {base_branch}")
            
            # Get repository
            repo = self.github.get_repo(repo_full_name)
            
            # Create PR
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
                draft=draft
            )
            
            logger.info(f"PR created successfully: #{pr.number}")
            
            return {
                "success": True,
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "message": f"Pull Request #{pr.number} created successfully"
            }
            
        except GithubException as e:
            logger.error(f"Failed to create PR: {e}")
            return {
                "success": False,
                "pr_number": None,
                "pr_url": None,
                "message": f"Failed to create PR: {e.data.get('message', str(e))}"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating PR: {e}")
            return {
                "success": False,
                "pr_number": None,
                "pr_url": None,
                "message": f"Unexpected error: {str(e)}"
            }
    
    def get_pull_request(
        self,
        repo_full_name: str,
        pr_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get Pull Request information
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: PR number
            
        Returns:
            PR information dict or None
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "head_branch": pr.head.ref,
                "base_branch": pr.base.ref,
                "url": pr.html_url,
                "created_at": pr.created_at,
                "updated_at": pr.updated_at,
                "merged": pr.merged,
                "draft": pr.draft,
                "mergeable": pr.mergeable,
                "mergeable_state": pr.mergeable_state
            }
            
        except GithubException as e:
            logger.error(f"Failed to get PR: {e}")
            return None
    
    def list_pull_requests(
        self,
        repo_full_name: str,
        state: str = "open",
        base_branch: Optional[str] = None,
        head_branch: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List Pull Requests
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            state: PR state (open, closed, all)
            base_branch: Filter by base branch
            head_branch: Filter by head branch
            
        Returns:
            List of PR information dicts
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            prs = repo.get_pulls(
                state=state,
                base=base_branch,
                head=head_branch
            )
            
            result = []
            for pr in prs:
                result.append({
                    "number": pr.number,
                    "title": pr.title,
                    "state": pr.state,
                    "head_branch": pr.head.ref,
                    "base_branch": pr.base.ref,
                    "url": pr.html_url,
                    "created_at": pr.created_at,
                    "merged": pr.merged,
                    "draft": pr.draft
                })
            
            return result
            
        except GithubException as e:
            logger.error(f"Failed to list PRs: {e}")
            return []
    
    def merge_pull_request(
        self,
        repo_full_name: str,
        pr_number: int,
        commit_message: Optional[str] = None,
        merge_method: str = "merge"
    ) -> Dict[str, Any]:
        """
        Merge a Pull Request
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: PR number to merge
            commit_message: Optional commit message
            merge_method: merge, squash, or rebase
            
        Returns:
            dict with merge result
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            
            result = pr.merge(
                commit_message=commit_message,
                merge_method=merge_method
            )
            
            if result.merged:
                logger.info(f"PR #{pr_number} merged successfully")
                return {
                    "success": True,
                    "message": f"PR #{pr_number} merged successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to merge PR #{pr_number}: {result.message}"
                }
                
        except GithubException as e:
            logger.error(f"Failed to merge PR: {e}")
            return {
                "success": False,
                "message": f"Failed to merge PR: {e.data.get('message', str(e))}"
            }
    
    def close_pull_request(
        self,
        repo_full_name: str,
        pr_number: int
    ) -> bool:
        """
        Close a Pull Request without merging
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            pr_number: PR number to close
            
        Returns:
            True if closed successfully
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            pr = repo.get_pull(pr_number)
            pr.edit(state="closed")
            
            logger.info(f"PR #{pr_number} closed successfully")
            return True
            
        except GithubException as e:
            logger.error(f"Failed to close PR: {e}")
            return False
