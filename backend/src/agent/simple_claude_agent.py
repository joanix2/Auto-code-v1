"""
Simple Claude Agent
Concrete implementation of BaseAgent using Claude Opus 4 and FileModificationService
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from anthropic import Anthropic

from .base_agent import BaseAgent
from ..models.ticket import Ticket
from ..models.message import Message
from ..services.utils.file_modification_service import FileModificationService

logger = logging.getLogger(__name__)


class SimpleClaudeAgent(BaseAgent):
    """
    Simple Claude-based agent for processing tickets and making code changes.
    
    This agent:
    1. Analyzes tickets using Claude Opus 4
    2. Generates code modifications in structured JSON format
    3. Applies changes using FileModificationService
    4. Validates the changes
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        workspace_root: str = "/tmp/autocode-workspace",
        model: str = "claude-opus-4-20250514"
    ):
        """
        Initialize Simple Claude Agent.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            workspace_root: Root directory for the agent's workspace
            model: Claude model to use
        """
        super().__init__(workspace_root)
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or provided")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        
        logger.info(f"SimpleClaudeAgent initialized with model {self.model}")
    
    def process_ticket(
        self,
        ticket: Ticket,
        repository_path: Path,
        initial_message: Optional[Message] = None
    ) -> Dict[str, Any]:
        """
        Process a ticket and make necessary changes.
        
        Args:
            ticket: Ticket to process
            repository_path: Path to the repository
            initial_message: Optional initial message/context
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing ticket {ticket.id}: {ticket.title}")
        
        try:
            # Step 1: Analyze ticket
            analysis = self.analyze_ticket(ticket, context=str(initial_message.content) if initial_message else None)
            logger.info(f"Analysis completed for ticket {ticket.id}")
            
            # Step 2: Generate code changes
            file_changes_json = self._generate_code_changes(ticket, analysis, repository_path)
            logger.info(f"Code changes generated for ticket {ticket.id}")
            
            # Step 3: Apply modifications using FileModificationService
            file_service = FileModificationService(str(repository_path))
            modification_results = file_service.apply_modifications(file_changes_json)
            
            if not modification_results.get("success"):
                return {
                    "success": False,
                    "files_modified": [],
                    "message": f"Failed to apply modifications: {modification_results.get('error')}",
                    "details": modification_results
                }
            
            # Get list of modified files
            files_modified = [
                result["path"]
                for result in modification_results.get("files_modified", [])
                if result.get("success")
            ]
            
            logger.info(f"Applied {len(files_modified)} file modifications for ticket {ticket.id}")
            
            # Step 4: Validate changes
            validation_results = self.validate_changes(repository_path, files_modified)
            
            # Generate summary
            summary = file_service.get_modified_files_summary(modification_results)
            
            return {
                "success": True,
                "files_modified": files_modified,
                "message": summary,
                "details": {
                    "analysis": analysis,
                    "modifications": modification_results,
                    "validation": validation_results
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing ticket {ticket.id}: {e}", exc_info=True)
            return {
                "success": False,
                "files_modified": [],
                "message": f"Error: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def analyze_ticket(self, ticket: Ticket, context: Optional[str] = None) -> str:
        """
        Analyze a ticket and create a plan.
        
        Args:
            ticket: Ticket to analyze
            context: Optional additional context
            
        Returns:
            Analysis and plan as a string
        """
        logger.info(f"Analyzing ticket: {ticket.title}")
        
        # Build analysis prompt
        context_section = f"**Additional Context:**\n{context}\n" if context else ""
        
        analysis_prompt = f"""You are an expert software developer analyzing a ticket for implementation.

**Ticket Information:**
- Title: {ticket.title}
- Type: {ticket.ticket_type}
- Priority: {ticket.priority}
- Description: {ticket.description}

{context_section}

**Task:**
1. Analyze the ticket requirements thoroughly
2. Break down the task into concrete steps
3. Identify files that need to be created or modified
4. Plan the implementation approach
5. Consider edge cases and potential issues

Provide a detailed analysis and step-by-step implementation plan.
Be specific about which files to modify and what changes to make.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3
            )
            
            analysis = response.content[0].text
            logger.info("Ticket analysis completed")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error during ticket analysis: {e}", exc_info=True)
            raise
    
    def _generate_code_changes(
        self,
        ticket: Ticket,
        analysis: str,
        repository_path: Path
    ) -> str:
        """
        Generate code changes based on analysis.
        
        Args:
            ticket: Ticket being processed
            analysis: Analysis from analyze_ticket()
            repository_path: Path to repository
            
        Returns:
            JSON string with file modifications
        """
        logger.info("Generating code changes")
        
        # Get repository structure for context
        repo_structure = self._get_repository_structure(repository_path)
        
        # Extract file mentions from analysis and read existing files
        existing_files_content = self._read_existing_files(repository_path, analysis)
        
        # Build existing files context
        files_context = ""
        if existing_files_content:
            files_context = "\n**Existing Files Content:**\n"
            for file_path, content in existing_files_content.items():
                files_context += f"\n--- {file_path} ---\n{content}\n"
        
        code_prompt = f"""Based on the following analysis, generate the necessary code changes.

**Analysis:**
{analysis}
{files_context}

**Repository Structure:**
{repo_structure}

**Instructions:**
1. PRESERVE existing code - only add, modify, or remove specific parts as needed
2. For existing files, keep all current functionality unless explicitly asked to change it
3. Add new functions/classes/features while maintaining existing ones
4. Follow best practices and coding standards
5. Include proper error handling
6. Add comments for complex logic
7. Ensure code is clean and maintainable

**CRITICAL:** When modifying existing files, you MUST:
- Read the existing file content provided above
- Keep all existing code that is not mentioned in the requirements
- Only add new features or modify specific parts as requested
- Preserve existing imports, functions, classes, and logic
- Do NOT regenerate or rewrite existing code unless specifically asked to refactor it

**IMPORTANT:** You MUST respond with ONLY valid JSON. No explanations before or after.

Format your response as JSON with this EXACT structure:
{{
  "files": [
    {{
      "path": "relative/path/to/file.py",
      "action": "create",
      "content": "complete file content here",
      "explanation": "brief explanation of what this file does"
    }},
    {{
      "path": "relative/path/to/existing_file.py",
      "action": "modify",
      "content": "complete file content with existing code PRESERVED and new additions",
      "explanation": "explanation of changes made"
    }}
  ],
  "summary": "Overall summary of changes"
}}

Remember: 
- Use "create" for new files, "modify" for existing files, "delete" to remove files
- For modified files: Include COMPLETE file content (existing + new changes)
- PRESERVE all existing code unless explicitly asked to change it
- Provide COMPLETE file content, not diffs
- Use relative paths from repository root
- Respond with ONLY the JSON, nothing else
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[
                    {
                        "role": "user",
                        "content": code_prompt
                    }
                ],
                temperature=0.2
            )
            
            code_changes = response.content[0].text
            logger.info("Code changes generated")
            
            return code_changes
            
        except Exception as e:
            logger.error(f"Error generating code changes: {e}", exc_info=True)
            raise
    
    def _read_existing_files(self, repository_path: Path, analysis: str) -> Dict[str, str]:
        """
        Read existing files that might be modified based on the analysis.
        
        Args:
            repository_path: Path to the repository
            analysis: Analysis text that may mention files
            
        Returns:
            Dictionary mapping file paths to their contents
        """
        import re
        
        existing_files = {}
        
        # Find potential file paths in the analysis (e.g., calculator.py, src/main.py, etc.)
        # Match patterns like: filename.ext, path/to/file.ext
        file_patterns = re.findall(r'\b([a-zA-Z0-9_/-]+\.[a-zA-Z0-9]+)\b', analysis)
        
        # Also scan for common Python files in the repository
        common_files_to_check = []
        try:
            for item in repository_path.rglob('*.py'):
                if any(ignore in str(item) for ignore in ['.git', '__pycache__', 'venv', '.venv', 'node_modules']):
                    continue
                # Get relative path
                rel_path = item.relative_to(repository_path)
                common_files_to_check.append(str(rel_path))
        except Exception as e:
            logger.warning(f"Error scanning repository: {e}")
        
        # Combine both sources
        files_to_check = set(file_patterns + common_files_to_check)
        
        for file_path_str in files_to_check:
            file_path = repository_path / file_path_str
            
            # Check if file exists and is readable
            if file_path.exists() and file_path.is_file():
                try:
                    # Read file content with size limit (max 50KB per file)
                    file_size = file_path.stat().st_size
                    if file_size > 50000:
                        logger.warning(f"Skipping large file: {file_path_str} ({file_size} bytes)")
                        continue
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        existing_files[file_path_str] = content
                        logger.info(f"Read existing file: {file_path_str} ({len(content)} chars)")
                        
                except Exception as e:
                    logger.warning(f"Could not read {file_path_str}: {e}")
        
        logger.info(f"Found {len(existing_files)} existing files to provide as context")
        return existing_files
    
    def _get_repository_structure(self, repository_path: Path, max_depth: int = 3) -> str:
        """
        Get a simplified view of the repository structure.
        
        Args:
            repository_path: Path to repository
            max_depth: Maximum directory depth to traverse
            
        Returns:
            String representation of repository structure
        """
        lines = []
        
        def walk_dir(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
                # Filter out common ignored directories
                items = [
                    item for item in items
                    if item.name not in {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}
                ]
                
                for i, item in enumerate(items[:20]):  # Limit items per directory
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = "    " if is_last else "│   "
                    
                    if item.is_dir():
                        lines.append(f"{prefix}{current_prefix}{item.name}/")
                        walk_dir(item, prefix + next_prefix, depth + 1)
                    else:
                        lines.append(f"{prefix}{current_prefix}{item.name}")
            except PermissionError:
                pass
        
        lines.append(repository_path.name + "/")
        walk_dir(repository_path)
        
        return "\n".join(lines[:100])  # Limit total lines
    
    def modify_files(
        self,
        repository_path: Path,
        file_changes: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Apply file modifications using FileModificationService.
        
        Args:
            repository_path: Path to the repository
            file_changes: List of file changes to apply
                
        Returns:
            List of modified file paths
        """
        logger.info(f"Applying {len(file_changes)} file modifications")
        
        # Convert file_changes to JSON format expected by FileModificationService
        modifications_json = {
            "files": file_changes,
            "summary": f"Applying {len(file_changes)} modifications"
        }
        
        import json
        file_service = FileModificationService(str(repository_path))
        results = file_service.apply_modifications(json.dumps(modifications_json))
        
        if not results.get("success"):
            logger.error(f"Failed to apply modifications: {results.get('error')}")
            raise Exception(f"File modifications failed: {results.get('error')}")
        
        modified_files = [
            result["path"]
            for result in results.get("files_modified", [])
            if result.get("success")
        ]
        
        logger.info(f"Successfully modified {len(modified_files)} files")
        return modified_files
    
    def validate_changes(
        self,
        repository_path: Path,
        modified_files: List[str]
    ) -> Dict[str, Any]:
        """
        Validate the changes made (basic validation).
        
        Args:
            repository_path: Path to the repository
            modified_files: List of modified file paths
            
        Returns:
            Validation results
        """
        logger.info(f"Validating {len(modified_files)} modified files")
        
        errors = []
        warnings = []
        
        # Basic validation: check if files exist and are readable
        for file_path in modified_files:
            full_path = repository_path / file_path
            
            if not full_path.exists():
                errors.append(f"File does not exist: {file_path}")
                continue
            
            if not full_path.is_file():
                errors.append(f"Path is not a file: {file_path}")
                continue
            
            # Check if file is readable
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    
                # Basic syntax check for Python files
                if file_path.endswith('.py'):
                    try:
                        compile(content, file_path, 'exec')
                    except SyntaxError as e:
                        errors.append(f"Python syntax error in {file_path}: {e}")
                        
            except Exception as e:
                errors.append(f"Error reading file {file_path}: {e}")
        
        is_valid = len(errors) == 0
        
        logger.info(f"Validation complete: {'PASSED' if is_valid else 'FAILED'} ({len(errors)} errors, {len(warnings)} warnings)")
        
        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "files_checked": len(modified_files)
        }
    
    def _get_capabilities(self) -> List[str]:
        """
        Get the capabilities of this agent.
        
        Returns:
            List of capability strings
        """
        return [
            "ticket_analysis",
            "code_generation",
            "file_modification",
            "python_syntax_validation",
            "claude_opus_4_integration"
        ]
