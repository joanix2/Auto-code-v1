"""
CI Service
Manages CI/CD operations and integrations
"""

import subprocess
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
from github import Github

logger = logging.getLogger(__name__)


class CIResult:
    """Result of a CI run"""
    
    def __init__(self, success: bool, message: str, details: Optional[Dict[str, Any]] = None):
        self.success = success
        self.failed = not success
        self.message = message
        self.details = details or {}
    
    def __repr__(self):
        return f"CIResult(success={self.success}, message='{self.message}')"


class CIService:
    """Service for CI/CD operations"""
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize CI service
        
        Args:
            github_token: GitHub token for API access
        """
        self.github_token = github_token
        self.github_client = Github(github_token) if github_token else None
    
    def run_ci(self, repo_path: Path, commit_hash: Optional[str] = None) -> CIResult:
        """
        Run CI checks on repository
        
        This method tries multiple CI strategies:
        1. Local tests (pytest, npm test, etc.)
        2. GitHub Actions status (if available)
        
        Args:
            repo_path: Path to repository
            commit_hash: Optional specific commit to check
            
        Returns:
            CIResult with success status and details
        """
        logger.info(f"Running CI checks for {repo_path}")
        
        # Try to run local tests first
        local_result = self._run_local_tests(repo_path)
        
        if local_result:
            return local_result
        
        # If we have GitHub integration, check Actions
        if self.github_client and commit_hash:
            github_result = self._check_github_actions(repo_path, commit_hash)
            if github_result:
                return github_result
        
        # Default: assume success if no tests found
        logger.warning("No CI tests found, assuming success")
        return CIResult(
            success=True,
            message="No CI configuration found",
            details={"note": "No tests were run"}
        )
    
    def _run_local_tests(self, repo_path: Path) -> Optional[CIResult]:
        """
        Run local tests (pytest, npm test, etc.)
        
        Args:
            repo_path: Path to repository
            
        Returns:
            CIResult if tests found and run, None otherwise
        """
        # Check for Python tests
        if (repo_path / "pytest.ini").exists() or \
           (repo_path / "setup.py").exists() or \
           (repo_path / "tests").exists():
            return self._run_pytest(repo_path)
        
        # Check for Node.js tests
        if (repo_path / "package.json").exists():
            return self._run_npm_test(repo_path)
        
        # Check for Makefile with test target
        if (repo_path / "Makefile").exists():
            return self._run_make_test(repo_path)
        
        return None
    
    def _run_pytest(self, repo_path: Path) -> CIResult:
        """Run pytest"""
        logger.info("Running pytest")
        
        try:
            result = subprocess.run(
                ['pytest', '-v', '--tb=short'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                return CIResult(
                    success=True,
                    message="All pytest tests passed",
                    details={
                        "stdout": result.stdout,
                        "test_framework": "pytest"
                    }
                )
            else:
                return CIResult(
                    success=False,
                    message="pytest tests failed",
                    details={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "test_framework": "pytest",
                        "exit_code": result.returncode
                    }
                )
        except subprocess.TimeoutExpired:
            return CIResult(
                success=False,
                message="pytest tests timed out (5 minutes)",
                details={"test_framework": "pytest", "error": "timeout"}
            )
        except FileNotFoundError:
            logger.warning("pytest not found, trying python -m pytest")
            try:
                result = subprocess.run(
                    ['python', '-m', 'pytest', '-v', '--tb=short'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                return CIResult(
                    success=result.returncode == 0,
                    message="Tests completed" if result.returncode == 0 else "Tests failed",
                    details={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "test_framework": "pytest"
                    }
                )
            except Exception as e:
                return CIResult(
                    success=False,
                    message=f"Failed to run pytest: {e}",
                    details={"error": str(e)}
                )
    
    def _run_npm_test(self, repo_path: Path) -> CIResult:
        """Run npm test"""
        logger.info("Running npm test")
        
        try:
            result = subprocess.run(
                ['npm', 'test'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return CIResult(
                    success=True,
                    message="All npm tests passed",
                    details={
                        "stdout": result.stdout,
                        "test_framework": "npm"
                    }
                )
            else:
                return CIResult(
                    success=False,
                    message="npm tests failed",
                    details={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "test_framework": "npm",
                        "exit_code": result.returncode
                    }
                )
        except subprocess.TimeoutExpired:
            return CIResult(
                success=False,
                message="npm tests timed out (5 minutes)",
                details={"test_framework": "npm", "error": "timeout"}
            )
        except FileNotFoundError:
            return CIResult(
                success=False,
                message="npm not found",
                details={"error": "npm_not_installed"}
            )
    
    def _run_make_test(self, repo_path: Path) -> CIResult:
        """Run make test"""
        logger.info("Running make test")
        
        try:
            result = subprocess.run(
                ['make', 'test'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return CIResult(
                    success=True,
                    message="Make test passed",
                    details={
                        "stdout": result.stdout,
                        "test_framework": "make"
                    }
                )
            else:
                return CIResult(
                    success=False,
                    message="Make test failed",
                    details={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "test_framework": "make",
                        "exit_code": result.returncode
                    }
                )
        except subprocess.TimeoutExpired:
            return CIResult(
                success=False,
                message="Make test timed out (5 minutes)",
                details={"test_framework": "make", "error": "timeout"}
            )
        except FileNotFoundError:
            return CIResult(
                success=False,
                message="make not found",
                details={"error": "make_not_installed"}
            )
    
    def _check_github_actions(self, repo_path: Path, commit_hash: str) -> Optional[CIResult]:
        """
        Check GitHub Actions status for a commit
        
        Args:
            repo_path: Path to repository
            commit_hash: Commit hash to check
            
        Returns:
            CIResult if Actions found, None otherwise
        """
        if not self.github_client:
            return None
        
        try:
            # Extract repo owner and name from git remote
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            # Parse github.com/owner/repo from URL
            if 'github.com' in remote_url:
                parts = remote_url.split('github.com')[1].strip('/:').replace('.git', '').split('/')
                if len(parts) >= 2:
                    owner, repo_name = parts[0], parts[1]
                    
                    repo = self.github_client.get_repo(f"{owner}/{repo_name}")
                    commit = repo.get_commit(commit_hash)
                    
                    # Wait a bit for Actions to start
                    time.sleep(5)
                    
                    # Get status
                    status = commit.get_combined_status()
                    
                    if status.state == "success":
                        return CIResult(
                            success=True,
                            message="GitHub Actions passed",
                            details={
                                "platform": "github_actions",
                                "state": status.state,
                                "total_count": status.total_count
                            }
                        )
                    elif status.state == "failure":
                        return CIResult(
                            success=False,
                            message="GitHub Actions failed",
                            details={
                                "platform": "github_actions",
                                "state": status.state,
                                "total_count": status.total_count
                            }
                        )
            
        except Exception as e:
            logger.warning(f"Could not check GitHub Actions: {e}")
        
        return None
    
    def create_ci_error_message(self, ci_result: CIResult) -> str:
        """
        Create a formatted error message from CI result
        
        Args:
            ci_result: Failed CI result
            
        Returns:
            Formatted error message for LLM
        """
        message = f"CI/CD Failed: {ci_result.message}\n\n"
        
        if ci_result.details.get("stderr"):
            message += "**Error Output:**\n```\n"
            message += ci_result.details["stderr"][:1000]  # Limit to 1000 chars
            message += "\n```\n\n"
        
        if ci_result.details.get("stdout"):
            message += "**Test Output:**\n```\n"
            message += ci_result.details["stdout"][:2000]  # Limit to 2000 chars
            message += "\n```\n\n"
        
        message += "Please analyze the errors and fix the code."
        
        return message
