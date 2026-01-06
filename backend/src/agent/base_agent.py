"""
Base Agent Interface
Abstract base class for all agent implementations
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..models.ticket import Ticket
from ..models.message import Message


class BaseAgent(ABC):
    """
    Abstract base class for agent implementations
    
    All agents must implement the core methods defined here.
    Agents are responsible for processing tickets and making code changes.
    """
    
    def __init__(self, workspace_root: str = "/tmp/autocode-workspace"):
        """
        Initialize the agent
        
        Args:
            workspace_root: Root directory for the agent's workspace
        """
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def process_ticket(
        self,
        ticket: Ticket,
        repository_path: Path,
        initial_message: Optional[Message] = None
    ) -> Dict[str, Any]:
        """
        Process a ticket and make necessary changes
        
        Args:
            ticket: Ticket to process
            repository_path: Path to the repository
            initial_message: Optional initial message/context
            
        Returns:
            Dictionary with processing results:
            {
                "success": bool,
                "files_modified": List[str],
                "message": str,
                "details": Any
            }
        """
        pass
    
    @abstractmethod
    def analyze_ticket(self, ticket: Ticket, context: Optional[str] = None) -> str:
        """
        Analyze a ticket and create a plan
        
        Args:
            ticket: Ticket to analyze
            context: Optional additional context
            
        Returns:
            Analysis and plan as a string
        """
        pass
    
    @abstractmethod
    def modify_files(
        self,
        repository_path: Path,
        file_changes: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Apply file modifications
        
        Args:
            repository_path: Path to the repository
            file_changes: List of file changes to apply
                Each change is a dict with:
                {
                    "file_path": str,
                    "action": "create" | "modify" | "delete",
                    "content": Optional[str]
                }
        
        Returns:
            List of modified file paths
        """
        pass
    
    @abstractmethod
    def validate_changes(
        self,
        repository_path: Path,
        modified_files: List[str]
    ) -> Dict[str, Any]:
        """
        Validate the changes made
        
        Args:
            repository_path: Path to the repository
            modified_files: List of modified file paths
            
        Returns:
            Validation results:
            {
                "valid": bool,
                "errors": List[str],
                "warnings": List[str]
            }
        """
        pass
    
    def get_agent_name(self) -> str:
        """
        Get the name of the agent
        
        Returns:
            Agent name
        """
        return self.__class__.__name__
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent
        
        Returns:
            Agent information dictionary
        """
        return {
            "name": self.get_agent_name(),
            "workspace_root": str(self.workspace_root),
            "capabilities": self._get_capabilities()
        }
    
    @abstractmethod
    def _get_capabilities(self) -> List[str]:
        """
        Get the capabilities of this agent
        
        Returns:
            List of capability strings
        """
        pass
