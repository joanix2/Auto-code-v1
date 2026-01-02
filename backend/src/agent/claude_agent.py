"""
Claude Opus 4 Agent with LangGraph
High-level AI agent for autonomous ticket development
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from anthropic import Anthropic
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..models.message import Message
from ..repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """State of the development agent"""
    ticket_id: str
    ticket_title: str
    ticket_description: str
    ticket_type: str
    priority: str
    
    repository_path: str
    repository_url: str
    
    messages: List[Dict[str, str]] = Field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 20
    
    current_task: Optional[str] = None
    code_changes: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    status: str = "initialized"  # initialized, analyzing, coding, testing, completed, failed
    final_output: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class ClaudeAgent:
    """
    Claude Opus 4 Agent for autonomous development
    Uses LangGraph for workflow orchestration
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude Agent
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or provided")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-20250514"  # Claude Opus 4.5
        
        logger.info(f"Initialized ClaudeAgent with model {self.model}")
    
    async def analyze_ticket(self, state: AgentState) -> AgentState:
        """
        First step: Analyze the ticket and create a development plan
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with analysis and plan
        """
        logger.info(f"Analyzing ticket: {state.ticket_id}")
        
        state.status = "analyzing"
        state.iterations += 1
        
        # Build analysis prompt
        analysis_prompt = f"""You are an expert software developer analyzing a ticket for implementation.

**Ticket Information:**
- Title: {state.ticket_title}
- Type: {state.ticket_type}
- Priority: {state.priority}
- Description: {state.ticket_description}

**Repository:** {state.repository_url}
**Local Path:** {state.repository_path}

**Task:**
1. Analyze the ticket requirements thoroughly
2. Break down the task into concrete steps
3. Identify files that need to be created or modified
4. Plan the implementation approach
5. Consider edge cases and potential issues

Provide a detailed analysis and step-by-step implementation plan.
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
            
            # Store in state
            state.messages.append({
                "role": "assistant",
                "content": analysis,
                "step": "analysis",
                "timestamp": datetime.now().isoformat()
            })
            
            # Persist to database
            message_repo = MessageRepository()
            message = Message(
                id="",
                ticket_id=state.ticket_id,
                role="assistant",
                content=analysis,
                model=self.model,
                tokens_used=response.usage.output_tokens if hasattr(response, 'usage') else None,
                step="analysis"
            )
            message_repo.create(message)
            
            state.current_task = "analysis_complete"
            logger.info("Ticket analysis completed")
            
        except Exception as e:
            logger.error(f"Error during ticket analysis: {e}")
            state.errors.append(f"Analysis failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def generate_code(self, state: AgentState) -> AgentState:
        """
        Second step: Generate code based on the analysis
        
        Args:
            state: Current agent state with analysis
            
        Returns:
            Updated state with generated code
        """
        logger.info(f"Generating code for ticket: {state.ticket_id}")
        
        state.status = "coding"
        state.iterations += 1
        
        # Get previous analysis
        analysis = next(
            (msg["content"] for msg in state.messages if msg.get("step") == "analysis"),
            "No analysis found"
        )
        
        coding_prompt = f"""Based on the following analysis, generate the necessary code changes.

**Analysis:**
{analysis}

**Instructions:**
1. Generate complete, production-ready code
2. Follow best practices and coding standards
3. Include proper error handling
4. Add comments for complex logic
5. Ensure code is clean and maintainable

For each file to be created or modified, provide:
- File path (relative to repository root)
- Complete file content
- Brief explanation of changes

Format your response as JSON with this structure:
{{
  "files": [
    {{
      "path": "relative/path/to/file.py",
      "action": "create|modify",
      "content": "complete file content",
      "explanation": "what this file does"
    }}
  ],
  "summary": "Overall summary of changes"
}}
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                messages=[
                    {
                        "role": "user",
                        "content": coding_prompt
                    }
                ],
                temperature=0.2
            )
            
            code_output = response.content[0].text
            
            # Store in state
            state.messages.append({
                "role": "assistant",
                "content": code_output,
                "step": "code_generation",
                "timestamp": datetime.now().isoformat()
            })
            
            # Persist to database
            message_repo = MessageRepository()
            message = Message(
                id="",
                ticket_id=state.ticket_id,
                role="assistant",
                content=code_output,
                model=self.model,
                tokens_used=response.usage.output_tokens if hasattr(response, 'usage') else None,
                step="code_generation"
            )
            message_repo.create(message)
            
            # Parse code changes (simplified - would need proper JSON parsing)
            state.code_changes.append({
                "iteration": state.iterations,
                "output": code_output,
                "timestamp": datetime.now().isoformat()
            })
            
            state.current_task = "code_generated"
            logger.info("Code generation completed")
            
        except Exception as e:
            logger.error(f"Error during code generation: {e}")
            state.errors.append(f"Code generation failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def review_and_test(self, state: AgentState) -> AgentState:
        """
        Third step: Review generated code and suggest tests
        
        Args:
            state: Current agent state with generated code
            
        Returns:
            Updated state with review and test suggestions
        """
        logger.info(f"Reviewing code for ticket: {state.ticket_id}")
        
        state.status = "testing"
        state.iterations += 1
        
        # Get generated code
        code_output = next(
            (msg["content"] for msg in state.messages if msg.get("step") == "code_generation"),
            "No code found"
        )
        
        review_prompt = f"""Review the following generated code and provide:

**Generated Code:**
{code_output}

**Review Points:**
1. Code quality and best practices
2. Potential bugs or issues
3. Security considerations
4. Performance implications
5. Test cases needed

Provide a comprehensive review and suggest any improvements or tests.
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": review_prompt
                    }
                ],
                temperature=0.3
            )
            
            review = response.content[0].text
            
            # Store in state
            state.messages.append({
                "role": "assistant",
                "content": review,
                "step": "review",
                "timestamp": datetime.now().isoformat()
            })
            
            # Persist to database
            message_repo = MessageRepository()
            message = Message(
                id="",
                ticket_id=state.ticket_id,
                role="assistant",
                content=review,
                model=self.model,
                tokens_used=response.usage.output_tokens if hasattr(response, 'usage') else None,
                step="review"
            )
            message_repo.create(message)
            
            state.current_task = "review_complete"
            state.status = "completed"
            logger.info("Code review completed")
            
        except Exception as e:
            logger.error(f"Error during code review: {e}")
            state.errors.append(f"Review failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    def should_continue(self, state: AgentState) -> str:
        """
        Decision function: determine if agent should continue or stop
        
        Args:
            state: Current agent state
            
        Returns:
            Next step name or END
        """
        # Check iteration limit
        if state.iterations >= state.max_iterations:
            logger.warning(f"Max iterations ({state.max_iterations}) reached")
            state.status = "failed"
            state.errors.append(f"Max iterations ({state.max_iterations}) exceeded")
            return END
        
        # Check for fatal errors
        if state.status == "failed":
            logger.error("Agent failed, stopping")
            return END
        
        # Check completion
        if state.status == "completed":
            logger.info("Agent completed successfully")
            return END
        
        # Determine next step based on current task
        if state.current_task == "analysis_complete":
            return "generate_code"
        elif state.current_task == "code_generated":
            return "review_and_test"
        elif state.current_task == "review_complete":
            return END
        
        # Default: continue with analysis
        return "analyze_ticket"
    
    async def run(
        self,
        ticket_id: str,
        ticket_title: str,
        ticket_description: str,
        ticket_type: str,
        priority: str,
        repository_path: str,
        repository_url: str,
        max_iterations: int = 20
    ) -> Dict[str, Any]:
        """
        Run the complete agent workflow
        
        Args:
            ticket_id: Unique ticket identifier
            ticket_title: Ticket title
            ticket_description: Ticket description
            ticket_type: Type of ticket (feature, bugfix, etc.)
            priority: Priority level
            repository_path: Local path to repository
            repository_url: GitHub repository URL
            max_iterations: Maximum number of iterations
            
        Returns:
            Final state with results
        """
        logger.info(f"Starting agent workflow for ticket {ticket_id}")
        
        # Initialize state
        initial_state = AgentState(
            ticket_id=ticket_id,
            ticket_title=ticket_title,
            ticket_description=ticket_description,
            ticket_type=ticket_type,
            priority=priority,
            repository_path=repository_path,
            repository_url=repository_url,
            max_iterations=max_iterations
        )
        
        # Build workflow graph
        from .workflow import build_development_workflow
        workflow = build_development_workflow(self)
        
        # Run workflow
        try:
            final_state = await workflow.ainvoke(initial_state)
            
            # Compile final output
            final_output = {
                "ticket_id": final_state.ticket_id,
                "status": final_state.status,
                "iterations": final_state.iterations,
                "messages": final_state.messages,
                "code_changes": final_state.code_changes,
                "errors": final_state.errors,
                "success": final_state.status == "completed"
            }
            
            logger.info(f"Agent workflow completed with status: {final_state.status}")
            return final_output
            
        except Exception as e:
            logger.error(f"Agent workflow failed: {e}")
            return {
                "ticket_id": ticket_id,
                "status": "failed",
                "iterations": 0,
                "messages": [],
                "code_changes": [],
                "errors": [str(e)],
                "success": False
            }
