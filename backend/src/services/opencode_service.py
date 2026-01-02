"""OpenCode Service - Integration with OpenCode AI in Docker"""
import os
import subprocess
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OpenCodeService:
    """Service for interacting with OpenCode AI running in Docker containers"""
    
    def __init__(self):
        """Initialize OpenCode service"""
        # Find the opencode-service directory relative to project root
        backend_dir = Path(__file__).parent.parent.parent  # backend/
        project_root = backend_dir.parent  # Auto-code-v1/
        self.service_dir = project_root / "opencode-service"
        
        self.manage_script = self.service_dir / "manage-opencode.sh"
        self.container_name = "autocode-opencode"
        self.workspace_dir = "/home/ubuntu/workspace"
        
        if not self.manage_script.exists():
            raise FileNotFoundError(
                f"OpenCode management script not found at {self.manage_script}"
            )
    
    async def ensure_container_running(self) -> bool:
        """
        Ensure the OpenCode container is running
        
        Returns:
            bool: True if container is running or successfully started
        """
        try:
            # Check container status
            result = await asyncio.create_subprocess_exec(
                str(self.manage_script),
                "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            # If container not running, start it
            if b"RUNNING" not in stdout:
                logger.info("Starting OpenCode container...")
                start_result = await asyncio.create_subprocess_exec(
                    str(self.manage_script),
                    "start",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await start_result.communicate()
                
                if start_result.returncode != 0:
                    logger.error("Failed to start OpenCode container")
                    return False
                
                logger.info("OpenCode container started successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring container is running: {e}")
            return False
    
    async def clone_or_update_repository(
        self,
        repo_url: str,
        github_token: Optional[str] = None
    ) -> Optional[str]:
        """
        Clone or update a repository in the container
        
        Args:
            repo_url: GitHub repository URL
            github_token: Optional GitHub token for authentication
        
        Returns:
            Path to repository in container, or None on failure
        """
        # Extract repo name from URL
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        repo_path = f"{self.workspace_dir}/{repo_name}"
        
        # Prepare git command with token if provided
        if github_token and "https://github.com" in repo_url:
            # Inject token into URL for authentication
            auth_url = repo_url.replace(
                "https://github.com",
                f"https://{github_token}@github.com"
            )
        else:
            auth_url = repo_url
        
        # Build clone/pull command
        git_cmd = f"""
        cd {self.workspace_dir}
        if [ -d {repo_name} ]; then
            echo "Repository exists, pulling latest changes..."
            cd {repo_name} && git pull
        else
            echo "Cloning repository..."
            git clone {auth_url}
        fi
        """
        
        try:
            # Execute in container
            result = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                self.container_name,
                "/bin/bash",
                "-c",
                git_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.info(f"Repository ready: {repo_name}")
                return repo_path
            else:
                logger.error(f"Git operation failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error cloning/updating repository: {e}")
            return None
    
    async def develop_ticket(
        self,
        ticket_title: str,
        ticket_description: Optional[str],
        ticket_type: str,
        priority: str,
        repository_url: str,
        github_token: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Use OpenCode to develop a ticket implementation in isolated container
        
        Args:
            ticket_title: Ticket title
            ticket_description: Ticket description
            ticket_type: Type of ticket
            priority: Priority level
            repository_url: GitHub repository URL
            github_token: GitHub authentication token
            additional_context: Any additional context
        
        Returns:
            Result containing implementation details
        """
        # Ensure container is running
        if not await self.ensure_container_running():
            raise RuntimeError("Failed to start OpenCode container")
        
        # Clone/update repository
        repo_path = await self.clone_or_update_repository(repository_url, github_token)
        if not repo_path:
            raise RuntimeError("Failed to prepare repository")
        
        # Generate prompt for OpenCode
        prompt = self._generate_ticket_prompt(
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            ticket_type=ticket_type,
            priority=priority,
            additional_context=additional_context
        )
        
        # Execute OpenCode in container
        # Note: We create a temporary file with the prompt to avoid shell escaping issues
        import base64
        prompt_b64 = base64.b64encode(prompt.encode()).decode()
        
        opencode_cmd = f"""
        cd {repo_path}
        echo '{prompt_b64}' | base64 -d > /tmp/opencode_prompt.txt
        /home/ubuntu/.opencode/bin/opencode run "$(cat /tmp/opencode_prompt.txt)"
        rm /tmp/opencode_prompt.txt
        """
        
        try:
            result = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                "-i",
                self.container_name,
                "/bin/bash",
                "-c",
                opencode_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            return {
                "success": result.returncode == 0,
                "output": stdout.decode(),
                "errors": stderr.decode(),
                "repository_path": repo_path,
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"Error executing OpenCode: {e}")
            return {
                "success": False,
                "output": "",
                "errors": str(e),
                "repository_path": repo_path,
                "prompt": prompt
            }
    
    def _generate_ticket_prompt(
        self,
        ticket_title: str,
        ticket_description: Optional[str],
        ticket_type: str,
        priority: str,
        additional_context: Optional[str] = None
    ) -> str:
        """Generate a structured prompt for OpenCode"""
        
        type_labels = {
            "feature": "✨ Nouvelle fonctionnalité",
            "bugfix": "🐛 Correction de bug",
            "refactor": "♻️ Refactorisation",
            "documentation": "📚 Documentation"
        }
        
        priority_labels = {
            "critical": "🔴 CRITIQUE",
            "high": "🟠 HAUTE",
            "medium": "🟡 MOYENNE",
            "low": "🟢 BASSE"
        }
        
        prompt = f"""# Ticket de Développement - Auto-Code

**Titre:** {ticket_title}
**Type:** {type_labels.get(ticket_type, ticket_type)}
**Priorité:** {priority_labels.get(priority, priority)}

## Description

{ticket_description or "Aucune description fournie"}

## Instructions

Implémente cette fonctionnalité en suivant les meilleures pratiques:
- Code propre et maintenable
- Tests si applicable
- Documentation des changements
- Commits atomiques avec messages clairs

Avant de terminer:
1. Vérifie que le code compile/fonctionne
2. Commit tous les changements
3. Prépare un résumé des modifications
"""
        
        if additional_context:
            prompt += f"\n## Contexte Additionnel\n\n{additional_context}"
        
        return prompt
    
    async def get_container_status(self) -> Dict[str, Any]:
        """Get current status of OpenCode container"""
        try:
            result = await asyncio.create_subprocess_exec(
                str(self.manage_script),
                "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            return {
                "running": b"RUNNING" in stdout,
                "exists": b"exists" in stdout or b"RUNNING" in stdout,
                "output": stdout.decode()
            }
        except Exception as e:
            logger.error(f"Error getting container status: {e}")
            return {
                "running": False,
                "exists": False,
                "output": str(e)
            }
    
    async def cleanup(self):
        """Stop and remove the OpenCode container"""
        try:
            result = await asyncio.create_subprocess_exec(
                str(self.manage_script),
                "remove",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            logger.info("OpenCode container cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up container: {e}")
