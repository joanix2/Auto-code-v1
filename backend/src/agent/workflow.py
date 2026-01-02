"""
LangGraph Workflow Definition
Defines the state machine for autonomous development workflow
"""

import logging
from typing import Dict, Any, Callable

from langgraph.graph import StateGraph, END
from .claude_agent import AgentState, ClaudeAgent

logger = logging.getLogger(__name__)


class DevelopmentWorkflow:
    """
    LangGraph-based workflow for autonomous ticket development
    
    Workflow stages:
    1. analyze_ticket -> Analyze requirements and create plan
    2. generate_code -> Generate code based on analysis
    3. review_and_test -> Review code and suggest tests
    4. (conditional) -> END or retry based on results
    """
    
    def __init__(self, agent: ClaudeAgent):
        """
        Initialize workflow with Claude agent
        
        Args:
            agent: ClaudeAgent instance to use for execution
        """
        self.agent = agent
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state machine
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each stage
        workflow.add_node("analyze_ticket", self.agent.analyze_ticket)
        workflow.add_node("generate_code", self.agent.generate_code)
        workflow.add_node("review_and_test", self.agent.review_and_test)
        
        # Set entry point
        workflow.set_entry_point("analyze_ticket")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "analyze_ticket",
            self.agent.should_continue,
            {
                "generate_code": "generate_code",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "generate_code",
            self.agent.should_continue,
            {
                "review_and_test": "review_and_test",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "review_and_test",
            self.agent.should_continue,
            {
                END: END
            }
        )
        
        # Compile graph
        return workflow.compile()
    
    async def run(self, initial_state: AgentState) -> AgentState:
        """
        Execute the workflow
        
        Args:
            initial_state: Initial agent state
            
        Returns:
            Final agent state after workflow execution
        """
        logger.info(f"Starting workflow for ticket: {initial_state.ticket_id}")
        
        try:
            # Run the compiled graph
            final_state = await self.graph.ainvoke(initial_state)
            logger.info(f"Workflow completed with status: {final_state.status}")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            initial_state.status = "failed"
            initial_state.errors.append(f"Workflow error: {str(e)}")
            return initial_state


def build_development_workflow(agent: ClaudeAgent) -> StateGraph:
    """
    Factory function to build development workflow
    
    Args:
        agent: ClaudeAgent instance
        
    Returns:
        Compiled StateGraph for development workflow
    """
    workflow = DevelopmentWorkflow(agent)
    return workflow.graph


# Advanced workflow variations

class IterativeWorkflow(DevelopmentWorkflow):
    """
    Enhanced workflow with iterative refinement
    Allows the agent to refine code based on review feedback
    """
    
    def _build_graph(self) -> StateGraph:
        """Build graph with iteration support"""
        workflow = StateGraph(AgentState)
        
        # Add all nodes
        workflow.add_node("analyze_ticket", self.agent.analyze_ticket)
        workflow.add_node("generate_code", self.agent.generate_code)
        workflow.add_node("review_and_test", self.agent.review_and_test)
        
        # Add refinement node
        async def refine_code(state: AgentState) -> AgentState:
            """Refine code based on review feedback"""
            logger.info("Refining code based on review")
            state.current_task = "refining"
            # Re-run code generation with review context
            return await self.agent.generate_code(state)
        
        workflow.add_node("refine_code", refine_code)
        
        # Set entry point
        workflow.set_entry_point("analyze_ticket")
        
        # Add edges with iteration support
        workflow.add_conditional_edges(
            "analyze_ticket",
            self.agent.should_continue,
            {
                "generate_code": "generate_code",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "generate_code",
            self.agent.should_continue,
            {
                "review_and_test": "review_and_test",
                END: END
            }
        )
        
        # Review can lead to refinement or completion
        def should_refine(state: AgentState) -> str:
            """Decide if refinement is needed"""
            # Refine if we have errors and haven't exceeded iterations
            if state.errors and state.iterations < state.max_iterations - 5:
                return "refine_code"
            return self.agent.should_continue(state)
        
        workflow.add_conditional_edges(
            "review_and_test",
            should_refine,
            {
                "refine_code": "refine_code",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "refine_code",
            self.agent.should_continue,
            {
                "review_and_test": "review_and_test",
                END: END
            }
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
        
        # Add all nodes
        workflow.add_node("analyze_ticket", self.agent.analyze_ticket)
        
        # Generate tests first
        async def generate_tests(state: AgentState) -> AgentState:
            """Generate test cases before implementation"""
            logger.info("Generating tests (TDD approach)")
            state.current_task = "generating_tests"
            # Modify prompt to focus on tests
            return await self.agent.generate_code(state)
        
        workflow.add_node("generate_tests", generate_tests)
        workflow.add_node("generate_code", self.agent.generate_code)
        workflow.add_node("review_and_test", self.agent.review_and_test)
        
        # Set entry point
        workflow.set_entry_point("analyze_ticket")
        
        # Build TDD flow: analyze -> tests -> code -> review
        workflow.add_conditional_edges(
            "analyze_ticket",
            self.agent.should_continue,
            {
                "generate_tests": "generate_tests",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "generate_tests",
            self.agent.should_continue,
            {
                "generate_code": "generate_code",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "generate_code",
            self.agent.should_continue,
            {
                "review_and_test": "review_and_test",
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "review_and_test",
            self.agent.should_continue,
            {
                END: END
            }
        )
        
        return workflow.compile()


# Export workflow builders
__all__ = [
    "DevelopmentWorkflow",
    "IterativeWorkflow",
    "TestDrivenWorkflow",
    "build_development_workflow"
]
