"""
Git Service
Manages Git operations for repositories
"""

import os
import subprocess
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class GitService:
    """Service for Git operations on repositories"""
    
    def __init__(self, workspace_root: str = "/tmp/autocode-workspace"):
        """
        Initialize Git service
        
        Args:
            workspace_root: Root directory for cloned repositories
        """
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
    
    def get_repo_path(self, repo_url: str) -> Path:
        """
        Get local path for a repository
        Uses owner/repo structure to avoid naming conflicts
        
        Args:
            repo_url: Repository URL (e.g., https://github.com/user/repo)
            
        Returns:
            Path to local repository
        """
        # Extract owner and repo name from URL
        # Supports: https://github.com/owner/repo or git@github.com:owner/repo
        url_clean = repo_url.rstrip('/').replace('.git', '')
        
        if 'github.com' in url_clean:
            # Extract from URL
            if ':' in url_clean and '@' in url_clean:
                # SSH format: git@github.com:owner/repo
                parts = url_clean.split(':')[1].split('/')
            else:
                # HTTPS format: https://github.com/owner/repo
                parts = url_clean.split('github.com/')[1].split('/')
            
            if len(parts) >= 2:
                owner = parts[0]
                repo_name = parts[1]
                # Create owner/repo directory structure
                return self.workspace_root / owner / repo_name
        
        # Fallback: just use repo name
        repo_name = url_clean.split('/')[-1]
        return self.workspace_root / repo_name
    
    def is_cloned(self, repo_url: str) -> bool:
        """
        Check if repository is already cloned
        
        Args:
            repo_url: Repository URL
            
        Returns:
            True if cloned, False otherwise
        """
        repo_path = self.get_repo_path(repo_url)
        return repo_path.exists() and (repo_path / '.git').exists()
    
    def clone(self, repo_url: str, token: Optional[str] = None) -> Path:
        """
        Clone a repository
        
        Args:
            repo_url: Repository URL
            token: Optional GitHub token for private repos
            
        Returns:
            Path to cloned repository
        """
        repo_path = self.get_repo_path(repo_url)
        
        if self.is_cloned(repo_url):
            logger.info(f"Repository already cloned at {repo_path}")
            return repo_path
        
        # Build clone URL with token if provided
        if token and 'github.com' in repo_url:
            clone_url = repo_url.replace('https://', f'https://{token}@')
        else:
            clone_url = repo_url
        
        logger.info(f"Cloning {repo_url} to {repo_path}")
        
        try:
            subprocess.run(
                ['git', 'clone', clone_url, str(repo_path)],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully cloned to {repo_path}")
            return repo_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            raise RuntimeError(f"Git clone failed: {e.stderr}")
    
    def pull(self, repo_url: str) -> None:
        """
        Pull latest changes from remote
        
        Args:
            repo_url: Repository URL
        """
        repo_path = self.get_repo_path(repo_url)
        
        if not self.is_cloned(repo_url):
            raise ValueError(f"Repository not cloned: {repo_url}")
        
        logger.info(f"Pulling latest changes for {repo_url}")
        
        try:
            subprocess.run(
                ['git', 'pull'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Successfully pulled latest changes")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull: {e.stderr}")
            raise RuntimeError(f"Git pull failed: {e.stderr}")
    
    def clone_or_pull(self, repo_url: str, token: Optional[str] = None, force: bool = False, dest_path: Optional[Path] = None) -> tuple[Path, bool]:
        """
        Clone a repository if not exists, otherwise pull latest changes
        
        Args:
            repo_url: Repository URL
            token: Optional GitHub token for private repos
            force: If True, clone even if already exists
            dest_path: Optional custom destination path (overrides default owner/repo structure)
            
        Returns:
            Tuple of (repo_path, is_new_clone)
            - repo_path: Path to the repository
            - is_new_clone: True if repository was cloned, False if pulled
        """
        # Use custom path if provided, otherwise use default
        if dest_path:
            repo_path = Path(dest_path)
            is_cloned = repo_path.exists() and (repo_path / '.git').exists()
        else:
            repo_path = self.get_repo_path(repo_url)
            is_cloned = self.is_cloned(repo_url)
        
        if is_cloned:
            if force:
                logger.info(f"Repository already cloned but force=True, pulling anyway")
                self._pull_at_path(repo_path)
                return repo_path, False
            else:
                logger.info(f"Repository already cloned, pulling latest changes")
                self._pull_at_path(repo_path)
                return repo_path, False
        else:
            logger.info(f"Repository not cloned, cloning now")
            if dest_path:
                cloned_path = self._clone_to_path(repo_url, dest_path, token=token)
            else:
                cloned_path = self.clone(repo_url, token=token)
            return cloned_path, True
    
    def _pull_at_path(self, repo_path: Path) -> None:
        """Pull latest changes at specific path"""
        logger.info(f"Pulling latest changes at {repo_path}")
        
        try:
            subprocess.run(
                ['git', 'pull'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Successfully pulled latest changes")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to pull: {e.stderr}")
            raise RuntimeError(f"Git pull failed: {e.stderr}")
    
    def _clone_to_path(self, repo_url: str, dest_path: Path, token: Optional[str] = None) -> Path:
        """Clone repository to specific path"""
        # Build clone URL with token if provided
        if token and 'github.com' in repo_url:
            clone_url = repo_url.replace('https://', f'https://{token}@')
        else:
            clone_url = repo_url
        
        logger.info(f"Cloning {repo_url} to {dest_path}")
        
        try:
            # Create parent directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            subprocess.run(
                ['git', 'clone', clone_url, str(dest_path)],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully cloned to {dest_path}")
            return dest_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            raise RuntimeError(f"Git clone failed: {e.stderr}")
    
    def branch_exists(self, repo_url: str, branch_name: str) -> bool:
        """
        Check if a branch exists
        
        Args:
            repo_url: Repository URL
            branch_name: Branch name to check
            
        Returns:
            True if branch exists, False otherwise
        """
        repo_path = self.get_repo_path(repo_url)
        
        try:
            result = subprocess.run(
                ['git', 'branch', '--list', branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False
    
    def create_branch(self, repo_url: str, branch_name: str, from_branch: str = "main") -> None:
        """
        Create a new branch
        
        Args:
            repo_url: Repository URL
            branch_name: Name of the new branch
            from_branch: Branch to create from (default: main)
        """
        repo_path = self.get_repo_path(repo_url)
        
        logger.info(f"Creating branch {branch_name} from {from_branch}")
        
        try:
            # Checkout base branch first
            subprocess.run(
                ['git', 'checkout', from_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Create and checkout new branch
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully created branch {branch_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch: {e.stderr}")
            raise RuntimeError(f"Git create branch failed: {e.stderr}")
    
    def checkout_branch(self, repo_url: str, branch_name: str) -> None:
        """
        Checkout an existing branch
        
        Args:
            repo_url: Repository URL
            branch_name: Branch name to checkout
        """
        repo_path = self.get_repo_path(repo_url)
        
        logger.info(f"Checking out branch {branch_name}")
        
        try:
            subprocess.run(
                ['git', 'checkout', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully checked out {branch_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to checkout branch: {e.stderr}")
            raise RuntimeError(f"Git checkout failed: {e.stderr}")
    
    def rebase_branch(self, repo_url: str, branch_name: str, onto_branch: str = "main") -> None:
        """
        Rebase a branch onto another branch
        
        Args:
            repo_url: Repository URL
            branch_name: Branch to rebase
            onto_branch: Branch to rebase onto (default: main)
        """
        repo_path = self.get_repo_path(repo_url)
        
        logger.info(f"Rebasing {branch_name} onto {onto_branch}")
        
        try:
            # First checkout the branch to rebase
            subprocess.run(
                ['git', 'checkout', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Rebase
            subprocess.run(
                ['git', 'rebase', onto_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully rebased {branch_name} onto {onto_branch}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to rebase: {e.stderr}")
            # Try to abort rebase if it failed
            try:
                subprocess.run(
                    ['git', 'rebase', '--abort'],
                    cwd=repo_path,
                    capture_output=True
                )
            except:
                pass
            raise RuntimeError(f"Git rebase failed: {e.stderr}")
    
    def commit_changes(self, repo_url: str, message: str, author_name: str = "AutoCode Bot", 
                      author_email: str = "bot@autocode.dev") -> str:
        """
        Commit all changes
        
        Args:
            repo_url: Repository URL
            message: Commit message
            author_name: Author name
            author_email: Author email
            
        Returns:
            Commit hash
        """
        repo_path = self.get_repo_path(repo_url)
        
        logger.info(f"Committing changes: {message}")
        
        try:
            # Stage all changes
            subprocess.run(
                ['git', 'add', '.'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Commit
            subprocess.run(
                ['git', 'commit', '-m', message, 
                 f'--author={author_name} <{author_email}>'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            commit_hash = result.stdout.strip()
            logger.info(f"Successfully committed: {commit_hash}")
            return commit_hash
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e.stderr}")
            raise RuntimeError(f"Git commit failed: {e.stderr}")
    
    def push_branch(self, repo_url: str, branch_name: str, token: Optional[str] = None) -> None:
        """
        Push branch to remote
        
        Args:
            repo_url: Repository URL
            branch_name: Branch to push
            token: Optional GitHub token
        """
        repo_path = self.get_repo_path(repo_url)
        
        logger.info(f"Pushing branch {branch_name}")
        
        try:
            # Set remote URL with token if provided
            if token:
                remote_url = repo_url.replace('https://', f'https://{token}@')
                subprocess.run(
                    ['git', 'remote', 'set-url', 'origin', remote_url],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            # Push
            subprocess.run(
                ['git', 'push', '-u', 'origin', branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Successfully pushed {branch_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push: {e.stderr}")
            raise RuntimeError(f"Git push failed: {e.stderr}")
    
    def get_current_branch(self, repo_url: str) -> str:
        """
        Get current branch name
        
        Args:
            repo_url: Repository URL
            
        Returns:
            Current branch name
        """
        repo_path = self.get_repo_path(repo_url)
        
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
            raise RuntimeError(f"Git branch check failed: {e.stderr}")
    
    def has_uncommitted_changes(self, repo_url: str) -> bool:
        """
        Check if there are uncommitted changes
        
        Args:
            repo_url: Repository URL
            
        Returns:
            True if there are uncommitted changes
        """
        repo_path = self.get_repo_path(repo_url)
        
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            return bool(result.stdout.strip())
        except subprocess.CalledProcessError:
            return False
    
    def merge_branch(
        self,
        repo_url: str,
        source_branch: str,
        target_branch: str = "main",
        fast_forward: bool = False
    ) -> dict:
        """
        Merge a branch into another branch
        
        Args:
            repo_url: Repository URL
            source_branch: Branch to merge from
            target_branch: Branch to merge into (default: main)
            fast_forward: If True, only do fast-forward merge
            
        Returns:
            dict with merge result:
            {
                "success": bool,
                "message": str,
                "conflicts": List[str]  # List of conflicting files if any
            }
        """
        repo_path = self.get_repo_path(repo_url)
        
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository not cloned: {repo_url}")
        
        try:
            # Checkout target branch
            logger.info(f"Checking out {target_branch}")
            subprocess.run(
                ['git', 'checkout', target_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Pull latest changes on target branch
            logger.info(f"Pulling latest changes on {target_branch}")
            subprocess.run(
                ['git', 'pull', 'origin', target_branch],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Perform merge
            merge_args = ['git', 'merge']
            if fast_forward:
                merge_args.append('--ff-only')
            else:
                merge_args.append('--no-ff')
            
            merge_args.append(source_branch)
            
            logger.info(f"Merging {source_branch} into {target_branch}")
            result = subprocess.run(
                merge_args,
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully merged {source_branch} into {target_branch}")
                return {
                    "success": True,
                    "message": f"Successfully merged {source_branch} into {target_branch}",
                    "conflicts": []
                }
            else:
                # Check for conflicts
                conflicts_result = subprocess.run(
                    ['git', 'diff', '--name-only', '--diff-filter=U'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                conflicts = conflicts_result.stdout.strip().split('\n') if conflicts_result.stdout.strip() else []
                
                logger.error(f"Merge conflicts detected: {conflicts}")
                return {
                    "success": False,
                    "message": f"Merge conflicts detected",
                    "conflicts": conflicts
                }
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Git merge failed: {e.stderr}")
            raise RuntimeError(f"Git merge failed: {e.stderr}")
    
    def abort_merge(self, repo_url: str) -> None:
        """
        Abort an ongoing merge
        
        Args:
            repo_url: Repository URL
        """
        repo_path = self.get_repo_path(repo_url)
        
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository not cloned: {repo_url}")
        
        try:
            logger.info("Aborting merge")
            subprocess.run(
                ['git', 'merge', '--abort'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info("Merge aborted successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to abort merge: {e.stderr}")
            raise RuntimeError(f"Failed to abort merge: {e.stderr}")
    
    def add_commit_and_push(
        self,
        repo_url: str,
        commit_message: str,
        branch_name: Optional[str] = None,
        author_name: str = "AutoCode Bot",
        author_email: str = "bot@autocode.dev",
        files: Optional[List[str]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add, commit and push changes in one operation
        
        Args:
            repo_url: Repository URL
            commit_message: Commit message
            branch_name: Branch to push to (uses current branch if None)
            author_name: Author name for commit
            author_email: Author email for commit
            files: Specific files to add (None = add all changes)
            token: Optional GitHub token for push
            
        Returns:
            dict with operation results:
            {
                "success": bool,
                "commit_hash": str,
                "branch": str,
                "message": str
            }
        """
        repo_path = self.get_repo_path(repo_url)
        
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository not cloned: {repo_url}")
        
        try:
            # Check if there are changes to commit
            if not self.has_uncommitted_changes(repo_url):
                logger.warning("No uncommitted changes found")
                return {
                    "success": False,
                    "commit_hash": None,
                    "branch": None,
                    "message": "No uncommitted changes to commit"
                }
            
            # Stage files
            if files:
                # Add specific files
                logger.info(f"Staging specific files: {files}")
                subprocess.run(
                    ['git', 'add'] + files,
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                # Add all changes
                logger.info("Staging all changes")
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            # Commit changes
            logger.info(f"Committing: {commit_message}")
            subprocess.run(
                ['git', 'commit', '-m', commit_message,
                 f'--author={author_name} <{author_email}>'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Get commit hash
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            commit_hash = result.stdout.strip()
            
            # Get current branch if not specified
            if not branch_name:
                branch_name = self.get_current_branch(repo_url)
            
            # Push to remote
            logger.info(f"Pushing to {branch_name}")
            try:
                self.push_branch(repo_url, branch_name, token)
            except RuntimeError as e:
                return {
                    "success": False,
                    "commit_hash": commit_hash,
                    "branch": branch_name,
                    "message": f"Committed but push failed: {str(e)}"
                }
            
            logger.info(f"Successfully added, committed ({commit_hash[:7]}) and pushed to {branch_name}")
            
            return {
                "success": True,
                "commit_hash": commit_hash,
                "branch": branch_name,
                "message": f"Successfully committed and pushed to {branch_name}"
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e.stderr}")
            return {
                "success": False,
                "commit_hash": None,
                "branch": None,
                "message": f"Git operation failed: {e.stderr}"
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "commit_hash": None,
                "branch": None,
                "message": f"Unexpected error: {str(e)}"
            }
