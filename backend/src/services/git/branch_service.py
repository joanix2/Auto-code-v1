"""
Branch Service
Manages Git branches for tickets
"""

import logging
from typing import Optional, Tuple
from pathlib import Path

from .git_service import GitService
from ...repositories.ticket_repository import TicketRepository
from ...models.ticket import Ticket

logger = logging.getLogger(__name__)


class BranchService:
    """Service for managing ticket branches"""
    
    def __init__(
        self,
        git_service: Optional[GitService] = None,
        ticket_repo: Optional[TicketRepository] = None,
        workspace_root: str = "/tmp/autocode-workspace"
    ):
        """
        Initialize branch service
        
        Args:
            git_service: Optional GitService instance
            ticket_repo: Optional TicketRepository instance
            workspace_root: Root directory for repositories
        """
        self.git_service = git_service or GitService(workspace_root=workspace_root)
        self.ticket_repo = ticket_repo
        self.workspace_root = Path(workspace_root)
    
    def get_branch_name_for_ticket(self, ticket: Ticket) -> str:
        """
        Generate a branch name for a ticket
        
        Args:
            ticket: Ticket object
            
        Returns:
            Branch name in format: ticket/<ticket-id>-<sanitized-title>
            
        Examples:
            >>> ticket = Ticket(id="abc123", title="Fix login bug")
            >>> service.get_branch_name_for_ticket(ticket)
            'ticket/abc123-fix-login-bug'
        """
        # Sanitize title: lowercase, replace spaces/special chars with dashes
        sanitized_title = ticket.title.lower()
        sanitized_title = ''.join(c if c.isalnum() or c == ' ' else '' for c in sanitized_title)
        sanitized_title = '-'.join(sanitized_title.split())[:50]  # Max 50 chars
        
        # Use first 8 chars of ticket ID
        short_id = ticket.id[:8]
        
        return f"ticket/{short_id}-{sanitized_title}"
    
    def ensure_branch_for_ticket(
        self,
        ticket: Ticket,
        repo_url: str,
        base_branch: str = "main"
    ) -> Tuple[str, bool]:
        """
        Ensure a branch exists for a ticket and checkout to it
        Creates the branch if it doesn't exist, otherwise checks it out
        
        Args:
            ticket: Ticket object
            repo_url: Repository URL
            base_branch: Base branch to create from (default: main)
            
        Returns:
            Tuple of (branch_name, was_created)
            - branch_name: Name of the branch
            - was_created: True if branch was created, False if it already existed
            
        Examples:
            >>> ticket = Ticket(id="abc123", title="Add feature")
            >>> branch, created = service.ensure_branch_for_ticket(ticket, repo_url)
            >>> print(f"Branch: {branch}, Created: {created}")
        """
        branch_name = self.get_branch_name_for_ticket(ticket)
        
        logger.info(f"Ensuring branch {branch_name} for ticket {ticket.id}")
        
        # Check if branch exists
        exists = self.git_service.branch_exists(repo_url, branch_name)
        
        if exists:
            logger.info(f"Branch {branch_name} already exists, checking out")
            self.git_service.checkout_branch(repo_url, branch_name)
            return branch_name, False
        else:
            logger.info(f"Branch {branch_name} does not exist, creating from {base_branch}")
            self.git_service.create_branch(repo_url, branch_name, from_branch=base_branch)
            return branch_name, True
    
    def checkout_ticket_branch(self, ticket: Ticket, repo_url: str) -> str:
        """
        Checkout the branch for a ticket (must already exist)
        
        Args:
            ticket: Ticket object
            repo_url: Repository URL
            
        Returns:
            Branch name that was checked out
            
        Raises:
            RuntimeError: If branch doesn't exist
        """
        branch_name = self.get_branch_name_for_ticket(ticket)
        
        if not self.git_service.branch_exists(repo_url, branch_name):
            raise RuntimeError(f"Branch {branch_name} does not exist for ticket {ticket.id}")
        
        logger.info(f"Checking out branch {branch_name} for ticket {ticket.id}")
        self.git_service.checkout_branch(repo_url, branch_name)
        
        return branch_name
    
    def create_ticket_branch(
        self,
        ticket: Ticket,
        repo_url: str,
        base_branch: str = "main",
        force: bool = False
    ) -> str:
        """
        Create a branch for a ticket
        
        Args:
            ticket: Ticket object
            repo_url: Repository URL
            base_branch: Base branch to create from
            force: If True, recreate branch even if it exists
            
        Returns:
            Branch name that was created
            
        Raises:
            RuntimeError: If branch already exists and force=False
        """
        branch_name = self.get_branch_name_for_ticket(ticket)
        
        exists = self.git_service.branch_exists(repo_url, branch_name)
        
        if exists and not force:
            raise RuntimeError(f"Branch {branch_name} already exists for ticket {ticket.id}")
        
        if exists and force:
            logger.warning(f"Branch {branch_name} exists but force=True, will recreate")
            # Delete and recreate (dangerous!)
            self._delete_branch(repo_url, branch_name)
        
        logger.info(f"Creating branch {branch_name} for ticket {ticket.id}")
        self.git_service.create_branch(repo_url, branch_name, from_branch=base_branch)
        
        return branch_name
    
    def _delete_branch(self, repo_url: str, branch_name: str) -> None:
        """Delete a branch (internal use only)"""
        import subprocess
        repo_path = self.git_service.get_repo_path(repo_url)
        
        try:
            subprocess.run(
                ['git', 'branch', '-D', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Deleted branch {branch_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete branch: {e.stderr}")
            raise RuntimeError(f"Git delete branch failed: {e.stderr}")
    
    def get_current_branch(self, repo_url: str) -> str:
        """
        Get the current branch name
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Current branch name
        """
        import subprocess
        repo_path = self.git_service.get_repo_path(repo_url)
        
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get current branch: {e.stderr}")
            raise RuntimeError(f"Git get current branch failed: {e.stderr}")
    
    def list_ticket_branches(self, repo_url: str) -> list[str]:
        """
        List all branches that match the ticket pattern
        
        Args:
            repo_url: Repository URL
            
        Returns:
            List of branch names matching pattern ticket/*
        """
        import subprocess
        repo_path = self.git_service.get_repo_path(repo_url)
        
        try:
            result = subprocess.run(
                ['git', 'branch', '--list', 'ticket/*'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            # Parse output, remove leading spaces and asterisks
            branches = [
                line.strip().lstrip('* ') 
                for line in result.stdout.split('\n') 
                if line.strip()
            ]
            return branches
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list branches: {e.stderr}")
            return []
    
    def get_branch_info(self, repo_url: str, branch_name: str) -> dict:
        """
        Get information about a branch
        
        Args:
            repo_url: Repository URL
            branch_name: Branch name
            
        Returns:
            Dictionary with branch information
        """
        import subprocess
        repo_path = self.git_service.get_repo_path(repo_url)
        
        try:
            # Get last commit info
            result = subprocess.run(
                ['git', 'log', '-1', '--format=%H|%an|%ae|%at|%s', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                commit_hash, author_name, author_email, timestamp, subject = result.stdout.strip().split('|')
                
                return {
                    "branch_name": branch_name,
                    "exists": True,
                    "last_commit": {
                        "hash": commit_hash,
                        "author_name": author_name,
                        "author_email": author_email,
                        "timestamp": int(timestamp),
                        "message": subject
                    }
                }
            else:
                return {"branch_name": branch_name, "exists": False}
                
        except subprocess.CalledProcessError:
            return {"branch_name": branch_name, "exists": False}
