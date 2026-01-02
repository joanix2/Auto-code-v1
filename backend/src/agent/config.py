"""
Claude Opus 4 Agent Configuration
Configuration file for the LangGraph-based development agent
"""

# Agent Configuration
CLAUDE_MODEL = "claude-opus-4-20250514"  # Claude Opus 4.5
MAX_ITERATIONS = 20  # Maximum workflow iterations
DEFAULT_TEMPERATURE = 0.3  # Lower for more deterministic output

# Token Limits
ANALYSIS_MAX_TOKENS = 4096
CODE_GENERATION_MAX_TOKENS = 8000
REVIEW_MAX_TOKENS = 4096

# Workflow Types
WORKFLOW_TYPES = {
    "standard": "DevelopmentWorkflow",  # Standard: analyze -> code -> review
    "iterative": "IterativeWorkflow",   # With refinement loops
    "tdd": "TestDrivenWorkflow"         # Test-Driven Development
}

DEFAULT_WORKFLOW = "standard"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
