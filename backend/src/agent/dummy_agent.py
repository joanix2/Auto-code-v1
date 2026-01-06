"""
Dummy Agent Implementation
Simple test agent that modifies a "toto" file
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent
from ..models.ticket import Ticket
from ..models.message import Message

logger = logging.getLogger(__name__)


class DummyAgent(BaseAgent):
    """
    Dummy agent for testing
    
    This agent simply creates/modifies a file named "toto" with 
    information about the ticket being processed.
    """
    
    def __init__(self, workspace_root: str = "/tmp/autocode-workspace"):
        """
        Initialize the dummy agent
        
        Args:
            workspace_root: Root directory for the agent's workspace
        """
        super().__init__(workspace_root)
        logger.info(f"DummyAgent initialized with workspace: {workspace_root}")
    
    def process_ticket(
        self,
        ticket: Ticket,
        repository_path: Path,
        initial_message: Optional[Message] = None
    ) -> Dict[str, Any]:
        """
        Process a ticket by modifying the "toto" file
        
        Args:
            ticket: Ticket to process
            repository_path: Path to the repository
            initial_message: Optional initial message
            
        Returns:
            Processing results
        """
        logger.info(f"Processing ticket: {ticket.id} - {ticket.title}")
        
        try:
            # Analyze the ticket
            analysis = self.analyze_ticket(ticket, initial_message.content if initial_message else None)
            
            # Define file change
            file_changes = [{
                "file_path": "toto",
                "action": "create",
                "content": self._generate_toto_content(ticket, analysis)
            }]
            
            # Modify files
            modified_files = self.modify_files(repository_path, file_changes)
            
            # Validate changes
            validation = self.validate_changes(repository_path, modified_files)
            
            return {
                "success": validation["valid"],
                "files_modified": modified_files,
                "message": f"DummyAgent processed ticket {ticket.id}",
                "details": {
                    "analysis": analysis,
                    "validation": validation
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing ticket: {e}")
            return {
                "success": False,
                "files_modified": [],
                "message": f"Error: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def analyze_ticket(self, ticket: Ticket, context: Optional[str] = None) -> str:
        """
        Analyze a ticket (dummy implementation)
        
        Args:
            ticket: Ticket to analyze
            context: Optional context
            
        Returns:
            Simple analysis text
        """
        analysis = f"""
=== DUMMY AGENT ANALYSIS ===

Ticket: {ticket.title}
ID: {ticket.id}
Type: {ticket.ticket_type.value if ticket.ticket_type else 'unknown'}
Priority: {ticket.priority.value if ticket.priority else 'unknown'}
Status: {ticket.status.value if ticket.status else 'unknown'}

Description:
{ticket.description or 'No description provided'}

Context:
{context or 'No context provided'}

Action Plan:
1. Create/modify file 'toto'
2. Write ticket information to file
3. Validate changes

=== END ANALYSIS ===
"""
        logger.info("Ticket analysis completed")
        return analysis.strip()
    
    def modify_files(
        self,
        repository_path: Path,
        file_changes: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Apply file modifications
        
        Args:
            repository_path: Path to the repository
            file_changes: List of changes to apply
            
        Returns:
            List of modified file paths
        """
        modified_files = []
        
        for change in file_changes:
            file_path = repository_path / change["file_path"]
            action = change["action"]
            content = change.get("content", "")
            
            try:
                if action == "create" or action == "modify":
                    # Create parent directories if needed
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write content
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    logger.info(f"{'Created' if action == 'create' else 'Modified'} file: {file_path}")
                    modified_files.append(str(file_path))
                    
                elif action == "delete":
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Deleted file: {file_path}")
                        modified_files.append(str(file_path))
                
            except Exception as e:
                logger.error(f"Error modifying file {file_path}: {e}")
                raise
        
        return modified_files
    
    def validate_changes(
        self,
        repository_path: Path,
        modified_files: List[str]
    ) -> Dict[str, Any]:
        """
        Validate the changes (dummy validation)
        
        Args:
            repository_path: Path to the repository
            modified_files: List of modified files
            
        Returns:
            Validation results
        """
        errors = []
        warnings = []
        
        # Check if files exist
        for file_path_str in modified_files:
            file_path = Path(file_path_str)
            if not file_path.exists():
                errors.append(f"File does not exist: {file_path}")
            else:
                # Check if file is readable
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if len(content) == 0:
                            warnings.append(f"File is empty: {file_path}")
                except Exception as e:
                    errors.append(f"Cannot read file {file_path}: {e}")
        
        is_valid = len(errors) == 0
        
        logger.info(f"Validation: {'PASSED' if is_valid else 'FAILED'} - {len(errors)} errors, {len(warnings)} warnings")
        
        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings
        }
    
    def _get_capabilities(self) -> List[str]:
        """
        Get agent capabilities
        
        Returns:
            List of capabilities
        """
        return [
            "create_files",
            "modify_files",
            "delete_files",
            "basic_validation"
        ]
    
    def _generate_toto_content(self, ticket: Ticket, analysis: str) -> str:
        """
        Generate content for the toto file
        
        Args:
            ticket: Ticket being processed
            analysis: Analysis text
            
        Returns:
            Content for toto file
        """
        content = f"""╔════════════════════════════════════════════════════════════════╗
║                    DUMMY AGENT - TOTO FILE                     ║
╚════════════════════════════════════════════════════════════════╝

Generated: {datetime.utcnow().isoformat()}
Agent: {self.get_agent_name()}

────────────────────────────────────────────────────────────────

TICKET INFORMATION:

  Title: {ticket.title}
  ID: {ticket.id}
  Type: {ticket.ticket_type.value if ticket.ticket_type else 'N/A'}
  Priority: {ticket.priority.value if ticket.priority else 'N/A'}
  Status: {ticket.status.value if ticket.status else 'N/A'}

  Description:
  {ticket.description or 'No description'}

────────────────────────────────────────────────────────────────

ANALYSIS:

{analysis}

────────────────────────────────────────────────────────────────

This file was automatically generated by DummyAgent.
It demonstrates the basic agent interface implementation.

╔════════════════════════════════════════════════════════════════╗
║                         END OF FILE                            ║
╚════════════════════════════════════════════════════════════════╝
"""
        return content
