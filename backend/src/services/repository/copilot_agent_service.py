"""
GitHub Copilot Agent Service
Gère l'interaction avec l'API GitHub Copilot Coding Agent
"""
import httpx
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GitHubCopilotAgentService:
    """Service pour interagir avec GitHub Copilot Coding Agent"""
    
    def __init__(self, github_token: str):
        """
        Initialize the Copilot Agent service
        
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
    
    async def assign_issue_to_copilot(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        custom_instructions: Optional[str] = None,
        base_branch: Optional[str] = "main",
        custom_agent: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign a GitHub issue to Copilot coding agent
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            custom_instructions: Optional custom instructions for Copilot
            base_branch: Base branch for the PR (default: main)
            custom_agent: Optional custom agent ID
            model: Optional model to use
            
        Returns:
            Response from GitHub API
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/assignees"
            
            # L'assignee en REST est copilot-swe-agent[bot]
            payload: Dict[str, Any] = {
                "assignees": ["copilot-swe-agent[bot]"],
                "agent_assignment": {
                    "target_repo": f"{owner}/{repo}",
                    "base_branch": base_branch,
                    "custom_instructions": custom_instructions or "",
                    "custom_agent": custom_agent or "",
                    "model": model or "",
                }
            }
            
            logger.info(f"Assigning issue #{issue_number} to Copilot in {owner}/{repo}")
            logger.debug(f"Payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                assignees = [a.get("login") for a in result.get("assignees", [])]
                logger.info(f"Successfully assigned issue #{issue_number}. Assignees: {assignees}")
                return {
                    "success": True,
                    "issue_number": issue_number,
                    "assignees": result.get("assignees", []),
                    "message": f"Issue #{issue_number} assigned to Copilot coding agent"
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error assigning issue to Copilot: {e}")
            logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to assign issue to Copilot: {e.response.text}")
        except Exception as e:
            logger.error(f"Error assigning issue to Copilot: {e}")
            raise
    
    async def create_issue_and_assign_to_copilot(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        custom_instructions: Optional[str] = None,
        base_branch: Optional[str] = "main",
        labels: Optional[list] = None,
        custom_agent: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new GitHub issue and assign it to Copilot
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            custom_instructions: Optional custom instructions
            base_branch: Base branch for the PR
            labels: Optional labels for the issue
            custom_agent: Optional custom agent ID
            model: Optional model to use
            
        Returns:
            Created issue information
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/issues"
            
            payload: Dict[str, Any] = {
                "title": title,
                "body": body,
                "assignees": ["copilot-swe-agent[bot]"],
                "agent_assignment": {
                    "target_repo": f"{owner}/{repo}",
                    "base_branch": base_branch,
                    "custom_instructions": custom_instructions or "",
                    "custom_agent": custom_agent or "",
                    "model": model or "",
                }
            }
            
            if labels:
                payload["labels"] = labels
            
            logger.info(f"Creating issue and assigning to Copilot in {owner}/{repo}")
            logger.debug(f"Payload: {payload}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                assignees = [a.get("login") for a in result.get("assignees", [])]
                logger.info(f"Successfully created issue #{result['number']}. Assignees: {assignees}")
                return {
                    "success": True,
                    "issue_number": result["number"],
                    "issue_url": result["html_url"],
                    "title": result["title"],
                    "assignees": assignees,
                    "message": f"Issue #{result['number']} created and assigned to Copilot"
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating issue: {e}")
            logger.error(f"Response: {e.response.text}")
            raise Exception(f"Failed to create issue: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            raise
    
    async def check_copilot_agent_status(
        self,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """
        Check if Copilot coding agent is enabled for a repository via GraphQL
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Status information with enabled flag
        """
        try:
            # Utilise GraphQL pour vérifier suggestedActors (méthode fiable)
            graphql_url = "https://api.github.com/graphql"
            graphql_headers = {
                **self.headers,
                "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"
            }
            
            query = """
            query($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {
                  nodes {
                    login
                    __typename
                  }
                }
              }
            }
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    graphql_url,
                    headers=graphql_headers,
                    json={"query": query, "variables": {"owner": owner, "name": repo}},
                    timeout=30.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    return {
                        "enabled": False,
                        "message": "Error checking Copilot status via GraphQL"
                    }
                
                nodes = (data.get("data", {})
                            .get("repository", {})
                            .get("suggestedActors", {})
                            .get("nodes", []))
                
                # Cherche copilot-swe-agent dans les suggestedActors
                for node in nodes:
                    if node.get("login") == "copilot-swe-agent" and node.get("__typename") == "Bot":
                        logger.info(f"Copilot coding agent detected for {owner}/{repo}")
                        return {
                            "enabled": True,
                            "message": "Copilot coding agent is enabled for this repository"
                        }
                
                logger.warning(f"Copilot coding agent not found in suggestedActors for {owner}/{repo}")
                return {
                    "enabled": False,
                    "message": "Copilot coding agent is not available for this repository. Please ensure you have an active GitHub Copilot subscription and that the agent feature is enabled."
                }
                    
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "enabled": False,
                    "message": "Copilot coding agent is not available for this repository"
                }
            logger.error(f"Error checking Copilot status: {e}")
            raise
        except Exception as e:
            logger.error(f"Error checking Copilot status: {e}")
            raise
    
    async def get_pull_request_from_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get the pull request created by Copilot for an issue
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Pull request information if found
        """
        try:
            # Search for pull requests that mention this issue
            url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/timeline"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={
                        **self.headers,
                        "Accept": "application/vnd.github.mockingbird-preview+json"
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                events = response.json()
                
                # Look for cross-referenced events that link to a PR
                for event in events:
                    if event.get("event") == "cross-referenced":
                        source = event.get("source", {})
                        if source.get("type") == "issue" and "pull_request" in source.get("issue", {}):
                            pr = source["issue"]
                            return {
                                "number": pr["number"],
                                "url": pr["html_url"],
                                "title": pr["title"],
                                "state": pr["state"],
                                "created_at": pr["created_at"]
                            }
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting PR from issue: {e}")
            return None
