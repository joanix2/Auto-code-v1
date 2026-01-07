"""
Repository Initializer Service
Initialize empty GitHub repositories by creating initial commit with README.md
"""
import httpx
from typing import Dict, Any, Optional
import logging
import base64

logger = logging.getLogger(__name__)


class RepositoryInitializerService:
    """Service to initialize empty GitHub repositories"""
    
    def __init__(self, github_token: str):
        """
        Initialize the service
        
        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    async def check_repository_initialized(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Check if repository has any commits (is initialized)
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Dict with initialization status
        """
        try:
            async with httpx.AsyncClient() as client:
                # Try to get the default branch
                repo_response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if repo_response.status_code != 200:
                    return {
                        "initialized": False,
                        "error": "Cannot fetch repository info"
                    }
                
                repo_data = repo_response.json()
                default_branch = repo_data.get("default_branch")
                
                # Empty repos don't have a default branch or it's null
                if not default_branch:
                    return {
                        "initialized": False,
                        "empty": True,
                        "message": "Repository is empty (no commits)"
                    }
                
                # Try to get commits on default branch
                commits_response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/commits",
                    headers=self.headers,
                    timeout=10.0
                )
                
                if commits_response.status_code == 409:
                    # 409 Conflict means empty repository
                    return {
                        "initialized": False,
                        "empty": True,
                        "message": "Repository is empty (no commits)"
                    }
                
                if commits_response.status_code == 200:
                    commits = commits_response.json()
                    return {
                        "initialized": True,
                        "empty": False,
                        "commit_count": len(commits),
                        "default_branch": default_branch
                    }
                
                return {
                    "initialized": False,
                    "error": f"HTTP {commits_response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error checking repository initialization: {str(e)}")
            return {
                "initialized": False,
                "error": str(e)
            }
    
    async def initialize_repository(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        readme_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initialize an empty repository by creating README.md
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: "main")
            readme_content: Custom README content (optional)
            
        Returns:
            Dict with initialization result
        """
        try:
            # Check if already initialized
            check = await self.check_repository_initialized(owner, repo)
            if check.get("initialized"):
                return {
                    "success": True,
                    "already_initialized": True,
                    "message": "Repository already has commits",
                    "default_branch": check.get("default_branch")
                }
            
            # Generate default README content if not provided
            if not readme_content:
                readme_content = f"""# {repo}

This repository was automatically initialized.

## About

Repository: {owner}/{repo}

## Getting Started

Add your project description here.
"""
            
            # Encode README content in base64
            readme_base64 = base64.b64encode(readme_content.encode()).decode()
            
            async with httpx.AsyncClient() as client:
                # Create README.md via GitHub API
                create_response = await client.put(
                    f"{self.base_url}/repos/{owner}/{repo}/contents/README.md",
                    headers=self.headers,
                    json={
                        "message": "Initial commit: Add README.md",
                        "content": readme_base64,
                        "branch": branch
                    },
                    timeout=30.0
                )
                
                if create_response.status_code in [200, 201]:
                    result = create_response.json()
                    logger.info(f"✅ Repository {owner}/{repo} initialized successfully")
                    
                    return {
                        "success": True,
                        "already_initialized": False,
                        "message": "Repository initialized with README.md",
                        "branch": branch,
                        "commit": result.get("commit", {}),
                        "content_url": result.get("content", {}).get("html_url")
                    }
                else:
                    error_detail = create_response.text
                    logger.error(f"Failed to initialize repository: {error_detail}")
                    
                    return {
                        "success": False,
                        "error": f"HTTP {create_response.status_code}: {error_detail}",
                        "status_code": create_response.status_code
                    }
                
        except Exception as e:
            logger.error(f"Error initializing repository: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def ensure_repository_ready(
        self,
        owner: str,
        repo: str,
        auto_initialize: bool = True
    ) -> Dict[str, Any]:
        """
        Ensure repository is ready for Copilot (has commits)
        
        Args:
            owner: Repository owner
            repo: Repository name
            auto_initialize: If True, automatically initialize if empty
            
        Returns:
            Dict with readiness status
        """
        try:
            # Check current status
            check = await self.check_repository_initialized(owner, repo)
            
            if check.get("initialized"):
                return {
                    "ready": True,
                    "message": "Repository is ready (has commits)",
                    "default_branch": check.get("default_branch"),
                    "action_taken": None
                }
            
            if check.get("empty"):
                if auto_initialize:
                    logger.info(f"🔧 Auto-initializing empty repository {owner}/{repo}...")
                    init_result = await self.initialize_repository(owner, repo)
                    
                    if init_result.get("success"):
                        return {
                            "ready": True,
                            "message": "Repository initialized automatically",
                            "action_taken": "created_readme",
                            "branch": init_result.get("branch"),
                            "commit": init_result.get("commit")
                        }
                    else:
                        return {
                            "ready": False,
                            "message": "Failed to initialize repository",
                            "error": init_result.get("error"),
                            "manual_steps": [
                                f"1. Go to https://github.com/{owner}/{repo}",
                                "2. Click 'Add a README'",
                                "3. Commit the README file",
                                "4. Try again"
                            ]
                        }
                else:
                    return {
                        "ready": False,
                        "message": "Repository is empty (auto-initialize disabled)",
                        "manual_steps": [
                            f"1. Go to https://github.com/{owner}/{repo}",
                            "2. Click 'Add a README'",
                            "3. Commit the README file",
                            "4. Or enable auto_initialize=true"
                        ]
                    }
            
            # Unknown state
            return {
                "ready": False,
                "message": "Cannot determine repository status",
                "error": check.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error ensuring repository readiness: {str(e)}")
            return {
                "ready": False,
                "error": str(e)
            }
