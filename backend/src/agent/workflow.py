"""
LangGraph Workflow Definition
Defines the state machine for autonomous development workflow
Inspired by the quickstart command with real development steps
"""

import os
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from langgraph.graph import StateGraph, END
from .claude_agent import AgentState, ClaudeAgent
from ..services.git import GitService, PullRequestService
from ..services.messaging import MessageService
from ..models.message import Message

logger = logging.getLogger(__name__)


class DevelopmentWorkflow:
    """
    Complete autonomous development workflow
    
    Workflow stages (inspired by quickstart):
    1. analyze_ticket -> Analyze requirements and create plan
    2. create_branch -> Create/checkout feature branch
    3. generate_code -> Generate code based on analysis
    4. review_and_test -> Review code and run tests
    5. commit_and_push -> Commit and push changes
    6. create_pull_request -> Create PR on GitHub
    7. (conditional) -> END or retry based on results
    """
    
    def __init__(
        self,
        agent: ClaudeAgent,
        workspace_root: str = "/workspace",
        github_token: Optional[str] = None
    ):
        """
        Initialize workflow with Claude agent and services
        
        Args:
            agent: ClaudeAgent instance to use for execution
            workspace_root: Root directory for workspace
            github_token: GitHub token for authentication
        """
        self.agent = agent
        self.workspace_root = workspace_root
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        # Initialize services
        self.git_service = GitService(workspace_root)
        self.message_service = MessageService()
        if self.github_token:
            self.pr_service = PullRequestService(self.github_token)
        else:
            self.pr_service = None
            logger.warning("No GitHub token provided, PR creation will be skipped")
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the complete development workflow graph
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each stage
        workflow.add_node("analyze_ticket", self._analyze_ticket_wrapper)
        workflow.add_node("create_branch", self._create_branch)
        workflow.add_node("generate_code", self._generate_code_wrapper)
        workflow.add_node("review_and_test", self._review_and_test_wrapper)
        workflow.add_node("commit_and_push", self._commit_and_push)
        workflow.add_node("create_pull_request", self._create_pull_request)
        
        # Set entry point
        workflow.set_entry_point("analyze_ticket")
        
        # Build workflow chain
        workflow.add_conditional_edges(
            "analyze_ticket",
            self._should_continue,
            {
                "create_branch": "create_branch",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "create_branch",
            self._should_continue,
            {
                "generate_code": "generate_code",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "generate_code",
            self._should_continue,
            {
                "review_and_test": "review_and_test",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "review_and_test",
            self._should_continue,
            {
                "commit_and_push": "commit_and_push",
                "generate_code": "generate_code",  # Retry if issues found
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "commit_and_push",
            self._should_continue,
            {
                "create_pull_request": "create_pull_request",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "create_pull_request",
            self._should_continue,
            {
                END: END
            }
        )
        
        # Compile graph
        return workflow.compile()
    
    # Wrapper methods for each stage
    
    async def _analyze_ticket_wrapper(self, state: AgentState) -> AgentState:
        """Analyze ticket and create development plan"""
        logger.info("Step 1/6: Analyzing ticket requirements")
        state.current_task = "analyzing"
        
        # Call agent's analyze method
        state = await self.agent.analyze_ticket(state)
        
        # Add analysis message to ticket
        if state.analysis:
            self._add_message_to_ticket(
                state.ticket_id,
                f"Analysis completed:\n{state.analysis}",
                {"step": "analysis", "source": "workflow"}
            )
        
        return state
    
    async def _create_branch(self, state: AgentState) -> AgentState:
        """Create and checkout feature branch"""
        logger.info("Step 2/6: Creating feature branch")
        state.current_task = "creating_branch"
        
        try:
            # Get repository URL from state
            repo_url = state.repository_url
            ticket_id = state.ticket_id
            
            # Generate branch name
            branch_name = f"ticket-{ticket_id[:8]}"
            
            # Check if branch exists
            if not self.git_service.branch_exists(repo_url, branch_name):
                # Create branch
                self.git_service.create_branch(repo_url, branch_name, "main")
                logger.info(f"Created branch: {branch_name}")
            
            # Checkout branch
            self.git_service.checkout_branch(repo_url, branch_name)
            state.branch_name = branch_name
            
            self._add_message_to_ticket(
                state.ticket_id,
                f"Branch created and checked out: {branch_name}",
                {"step": "branch_creation", "branch": branch_name, "source": "workflow"}
            )
            
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            state.errors.append(f"Branch creation failed: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def _generate_code_wrapper(self, state: AgentState) -> AgentState:
        """Generate code based on analysis"""
        logger.info("Step 3/6: Generating code")
        state.current_task = "generating_code"
        
        # Call agent's code generation
        state = await self.agent.generate_code(state)
        
        # Add code generation message
        if state.code_changes:
            files_changed = len(state.code_changes)
            self._add_message_to_ticket(
                state.ticket_id,
                f"Code generation completed: {files_changed} file(s) modified",
                {"step": "code_generation", "files_count": files_changed, "source": "workflow"}
            )
        
        return state
    
    async def _review_and_test_wrapper(self, state: AgentState) -> AgentState:
        """Review code and run tests"""
        logger.info("Step 4/6: Reviewing code and running tests")
        state.current_task = "reviewing"
        
        # Call agent's review method
        state = await self.agent.review_and_test(state)
        
        # Add review message
        if state.review_results:
            self._add_message_to_ticket(
                state.ticket_id,
                f"Code review completed:\n{state.review_results}",
                {"step": "review", "source": "workflow"}
            )
        
        return state
    
    async def _commit_and_push(self, state: AgentState) -> AgentState:
        """Commit changes and push to remote"""
        logger.info("Step 5/6: Committing and pushing changes")
        state.current_task = "committing"
        
        try:
            repo_url = state.repository_url
            branch_name = state.branch_name or f"ticket-{state.ticket_id[:8]}"
            
            # Check for uncommitted changes
            if not self.git_service.has_uncommitted_changes(repo_url):
                logger.warning("No changes to commit")
                state.errors.append("No uncommitted changes found")
                return state
            
            # Generate commit message from ticket
            commit_message = f"feat: {state.ticket_title}\n\n{state.analysis or 'Automated code generation'}"
            
            # Add, commit and push
            result = self.git_service.add_commit_and_push(
                repo_url=repo_url,
                commit_message=commit_message,
                branch_name=branch_name,
                token=self.github_token
            )
            
            if result.get("success"):
                commit_hash = result.get("commit_hash", "")[:7]
                state.commit_hash = result.get("commit_hash")
                
                logger.info(f"Changes committed: {commit_hash}")
                
                self._add_message_to_ticket(
                    state.ticket_id,
                    f"Changes committed and pushed: {commit_hash}\n{commit_message}",
                    {
                        "step": "commit",
                        "commit_hash": result.get("commit_hash"),
                        "branch": branch_name,
                        "source": "workflow"
                    }
                )
            else:
                error_msg = result.get("message", "Unknown error")
                state.errors.append(f"Commit failed: {error_msg}")
                state.status = "failed"
                
        except Exception as e:
            logger.error(f"Commit and push failed: {e}")
            state.errors.append(f"Commit error: {str(e)}")
            state.status = "failed"
        
        return state
    
    async def _create_pull_request(self, state: AgentState) -> AgentState:
        """Create Pull Request on GitHub"""
        logger.info("Step 6/6: Creating Pull Request")
        state.current_task = "creating_pr"
        
        if not self.pr_service:
            logger.warning("PR service not available, skipping PR creation")
            state.errors.append("No GitHub token provided")
            return state
        
        try:
            # Extract repo owner/name from URL
            repo_full_name = state.repository_name
            branch_name = state.branch_name or f"ticket-{state.ticket_id[:8]}"
            
            # Prepare PR details
            pr_title = f"feat: {state.ticket_title}"
            pr_body = f"""## {state.ticket_title}

**Ticket ID:** {state.ticket_id}

### Analysis
{state.analysis or 'No analysis provided'}

### Changes
{state.review_results or 'Code generated by autonomous agent'}

### Files Modified
{len(state.code_changes or [])} file(s) changed

---
Automated PR created by AutoCode workflow
Closes #{state.ticket_id}
"""
            
            # Create PR
            result = self.pr_service.create_pull_request(
                repo_full_name=repo_full_name,
                title=pr_title,
                body=pr_body,
                head_branch=branch_name,
                base_branch="main",
                draft=False
            )
            
            if result.get("success"):
                pr_number = result.get("pr_number")
                pr_url = result.get("pr_url")
                state.pr_number = pr_number
                state.pr_url = pr_url
                state.status = "completed"
                
                logger.info(f"Pull Request created: #{pr_number}")
                
                self._add_message_to_ticket(
                    state.ticket_id,
                    f"Pull Request created: #{pr_number}\n{pr_url}",
                    {
                        "step": "pr_creation",
                        "pr_number": pr_number,
                        "pr_url": pr_url,
                        "source": "workflow"
                    }
                )
            else:
                error_msg = result.get("message", "Unknown error")
                state.errors.append(f"PR creation failed: {error_msg}")
                state.status = "failed"
                
        except Exception as e:
            logger.error(f"PR creation failed: {e}")
            state.errors.append(f"PR error: {str(e)}")
            state.status = "failed"
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine next step in workflow"""
        # Check for errors
        if state.status == "failed":
            logger.error(f"Workflow failed: {state.errors}")
            return END
        
        # Use agent's should_continue for analysis/generation/review stages
        if state.current_task in ["analyzing", "generating_code", "reviewing"]:
            next_step = self.agent.should_continue(state)
            if next_step == END:
                return END
        
        # Continue to next stage based on current task
        task_flow = {
            "analyzing": "create_branch",
            "creating_branch": "generate_code",
            "generating_code": "review_and_test",
            "reviewing": "commit_and_push" if not state.errors else "generate_code",
            "committing": "create_pull_request",
            "creating_pr": END
        }
        
        return task_flow.get(state.current_task, END)
    
    def _add_message_to_ticket(
        self,
        ticket_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Helper to add message to ticket"""
        try:
            message = Message(
                id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                role="system",
                content=content,
                timestamp=datetime.now(),
                metadata=metadata
            )
            self.message_service.create_message(message)
        except Exception as e:
            logger.error(f"Failed to add message to ticket: {e}")
    
    async def run(self, initial_state: AgentState) -> AgentState:
        """
        Execute the complete development workflow
        
        Args:
            initial_state: Initial agent state with ticket info
            
        Returns:
            Final agent state after workflow execution
        """
        logger.info(f"Starting complete development workflow for ticket: {initial_state.ticket_id}")
        logger.info(f"Repository: {initial_state.repository_name}")
        logger.info(f"Workspace: {self.workspace_root}")
        
        try:
            # Add initial message
            self._add_message_to_ticket(
                initial_state.ticket_id,
                f"Starting autonomous development workflow for: {initial_state.ticket_title}",
                {"step": "workflow_start", "source": "workflow"}
            )
            
            # Run the compiled graph
            final_state = await self.graph.ainvoke(initial_state)
            
            # Log completion
            logger.info(f"Workflow completed with status: {final_state.status}")
            
            # Add completion message
            if final_state.status == "completed":
                summary = f"""✅ Workflow completed successfully!

**Branch:** {final_state.branch_name}
**Commit:** {final_state.commit_hash[:7] if final_state.commit_hash else 'N/A'}
**Pull Request:** #{final_state.pr_number} ({final_state.pr_url})

All stages completed:
✓ Analysis
✓ Branch creation
✓ Code generation
✓ Review & testing
✓ Commit & push
✓ Pull Request created
"""
                self._add_message_to_ticket(
                    final_state.ticket_id,
                    summary,
                    {
                        "step": "workflow_complete",
                        "status": "success",
                        "pr_number": final_state.pr_number,
                        "pr_url": final_state.pr_url,
                        "source": "workflow"
                    }
                )
            else:
                error_summary = f"""❌ Workflow failed

**Errors:**
{chr(10).join(f'- {e}' for e in final_state.errors)}

**Last task:** {final_state.current_task}
"""
                self._add_message_to_ticket(
                    final_state.ticket_id,
                    error_summary,
                    {
                        "step": "workflow_failed",
                        "status": "failed",
                        "errors": final_state.errors,
                        "source": "workflow"
                    }
                )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            initial_state.status = "failed"
            initial_state.errors.append(f"Workflow error: {str(e)}")
            
            self._add_message_to_ticket(
                initial_state.ticket_id,
                f"❌ Workflow crashed: {str(e)}",
                {"step": "workflow_error", "status": "crashed", "error": str(e), "source": "workflow"}
            )
            
            return initial_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            initial_state.status = "failed"
            initial_state.errors.append(f"Workflow error: {str(e)}")
            return initial_state


def build_development_workflow(
    agent: ClaudeAgent,
    workspace_root: str = "/workspace",
    github_token: Optional[str] = None
) -> StateGraph:
    """
    Factory function to build complete development workflow
    
    Args:
        agent: ClaudeAgent instance
        workspace_root: Root directory for workspace
        github_token: GitHub token for authentication
        
    Returns:
        Compiled StateGraph for development workflow
    """
    workflow = DevelopmentWorkflow(agent, workspace_root, github_token)
    return workflow.graph


# Advanced workflow variations (updated to match new structure)

class IterativeWorkflow(DevelopmentWorkflow):
    """
    Enhanced workflow with iterative refinement
    Allows the agent to refine code based on review feedback
    """
    
    def _build_graph(self) -> StateGraph:
        """Build graph with iteration support"""
        workflow = StateGraph(AgentState)
        
        # Add all standard nodes
        workflow.add_node("analyze_ticket", self._analyze_ticket_wrapper)
        workflow.add_node("create_branch", self._create_branch)
        workflow.add_node("generate_code", self._generate_code_wrapper)
        workflow.add_node("review_and_test", self._review_and_test_wrapper)
        workflow.add_node("commit_and_push", self._commit_and_push)
        workflow.add_node("create_pull_request", self._create_pull_request)
        
        # Add refinement node
        async def refine_code(state: AgentState) -> AgentState:
            """Refine code based on review feedback"""
            logger.info("Refining code based on review feedback")
            state.current_task = "refining_code"
            state.iterations += 1
            
            # Re-run code generation with review context
            return await self._generate_code_wrapper(state)
        
        workflow.add_node("refine_code", refine_code)
        
        # Set entry point
        workflow.set_entry_point("analyze_ticket")
        
        # Build workflow with iteration
        workflow.add_conditional_edges(
            "analyze_ticket",
            lambda s: "create_branch" if s.status != "failed" else END,
            {"create_branch": "create_branch", END: END}
        )
        
        workflow.add_conditional_edges(
            "create_branch",
            lambda s: "generate_code" if s.status != "failed" else END,
            {"generate_code": "generate_code", END: END}
        )
        
        workflow.add_conditional_edges(
            "generate_code",
            lambda s: "review_and_test" if s.status != "failed" else END,
            {"review_and_test": "review_and_test", END: END}
        )
        
        # Review can lead to refinement or commit
        def should_refine(state: AgentState) -> str:
            """Decide if refinement is needed"""
            if state.status == "failed":
                return END
            # Refine if we have errors and haven't exceeded max iterations
            if state.errors and state.iterations < state.max_iterations - 3:
                return "refine_code"
            # Otherwise commit
            return "commit_and_push"
        
        workflow.add_conditional_edges(
            "review_and_test",
            should_refine,
            {
                "refine_code": "refine_code",
                "commit_and_push": "commit_and_push",
                END: END
            }
        )
        
        # Refinement goes back to review
        workflow.add_conditional_edges(
            "refine_code",
            lambda s: "review_and_test" if s.status != "failed" else END,
            {"review_and_test": "review_and_test", END: END}
        )
        
        workflow.add_conditional_edges(
            "commit_and_push",
            lambda s: "create_pull_request" if s.status != "failed" else END,
            {"create_pull_request": "create_pull_request", END: END}
        )
        
        workflow.add_conditional_edges(
            "create_pull_request",
            lambda s: END,
            {END: END}
        )
        
        return workflow.compile()


class TestDrivenWorkflow(DevelopmentWorkflow):
    """
    Test-Driven Development workflow
    Generates tests first, then implements code to pass tests
    """
    
    def _build_graph(self) -> StateGraph:
        """Build TDD workflow graph"""
        workflow = StateGraph(AgentState)
        
        # Add all standard nodes
        workflow.add_node("analyze_ticket", self._analyze_ticket_wrapper)
        workflow.add_node("create_branch", self._create_branch)
        workflow.add_node("generate_code", self._generate_code_wrapper)
        workflow.add_node("review_and_test", self._review_and_test_wrapper)
        workflow.add_node("commit_and_push", self._commit_and_push)
        workflow.add_node("create_pull_request", self._create_pull_request)
        
        # Generate tests first
        async def generate_tests(state: AgentState) -> AgentState:
            """Generate test cases before implementation"""
            logger.info("Generating tests (TDD approach)")
            state.current_task = "generating_tests"
            
            # Add context to focus on tests
            original_task = state.current_task
            state.current_task = "generating_tests"
            
            # Generate tests using code generation
            state = await self._generate_code_wrapper(state)
            
            self._add_message_to_ticket(
                state.ticket_id,
                "Test cases generated (TDD)",
                {"step": "test_generation", "source": "workflow"}
            )
            
            return state
        
        workflow.add_node("generate_tests", generate_tests)
        
        # Set entry point
        workflow.set_entry_point("analyze_ticket")
        
        # Build TDD flow: analyze -> branch -> tests -> code -> review -> commit -> PR
        workflow.add_conditional_edges(
            "analyze_ticket",
            lambda s: "create_branch" if s.status != "failed" else END,
            {"create_branch": "create_branch", END: END}
        )
        
        workflow.add_conditional_edges(
            "create_branch",
            lambda s: "generate_tests" if s.status != "failed" else END,
            {"generate_tests": "generate_tests", END: END}
        )
        
        workflow.add_conditional_edges(
            "generate_tests",
            lambda s: "generate_code" if s.status != "failed" else END,
            {"generate_code": "generate_code", END: END}
        )
        
        workflow.add_conditional_edges(
            "generate_code",
            lambda s: "review_and_test" if s.status != "failed" else END,
            {"review_and_test": "review_and_test", END: END}
        )
        
        workflow.add_conditional_edges(
            "review_and_test",
            lambda s: "commit_and_push" if s.status != "failed" and not s.errors else END,
            {"commit_and_push": "commit_and_push", END: END}
        )
        
        workflow.add_conditional_edges(
            "commit_and_push",
            lambda s: "create_pull_request" if s.status != "failed" else END,
            {"create_pull_request": "create_pull_request", END: END}
        )
        
        workflow.add_conditional_edges(
            "create_pull_request",
            lambda s: END,
            {END: END}
        )
        
        return workflow.compile()


# Export workflow builders
__all__ = [
    "DevelopmentWorkflow",
    "IterativeWorkflow",
    "TestDrivenWorkflow",
    "build_development_workflow"
]
