"""
Controllers - API Endpoints (Clean Architecture)
"""
from .oauth.auth_controller import router as auth_router
from .repository.repository_controller import router as repository_router
from .repository.issue_controller import router as issue_router
from .repository.message_controller import router as message_router
from .repository.copilot_assignment_controller import router as copilot_assignment_router

__all__ = [
    "auth_router",
    "repository_router",
    "issue_router",
    "message_router",
    "copilot_assignment_router",
]

