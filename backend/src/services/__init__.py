"""Package des services"""

# Git services
from .git import GitService, BranchService, GitHubService

# Messaging services
from .messaging import MessageService

# Utility services
from .utils import FileModificationService, ImageService, levenshtein_service

# Auth services
from .auth import GitHubOAuthService

# CI/CD services
from .ci import CIService

# AI services - lazy import to avoid langgraph dependency issues
def _lazy_import_ai():
    from .ai import ClaudeService, TicketProcessingService
    return ClaudeService, TicketProcessingService

# Workflow services - lazy import
def _lazy_import_workflows():
    from .workflows import TicketProcessingWorkflow
    return TicketProcessingWorkflow

__all__ = [
    # Git
    "GitService",
    "BranchService",
    "GitHubService",
    # Messaging
    "MessageService",
    # Utils
    "FileModificationService",
    "ImageService",
    "levenshtein_service",
    # Auth
    "GitHubOAuthService",
    # CI
    "CIService",
    # AI - lazy loaded
    "ClaudeService",
    "TicketProcessingService",
    # Workflows - lazy loaded
    "TicketProcessingWorkflow",
]

# Export lazy imports
def __getattr__(name):
    if name == "ClaudeService":
        ClaudeService, _ = _lazy_import_ai()
        return ClaudeService
    elif name == "TicketProcessingService":
        _, TicketProcessingService = _lazy_import_ai()
        return TicketProcessingService
    elif name == "TicketProcessingWorkflow":
        return _lazy_import_workflows()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

